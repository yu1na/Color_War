import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer

from hdbscan import HDBSCAN

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

STOP_WORDS = [
    "그리고",
    "그래서",
    "그러나",
    "이제",
    "하지만",
    "정말",
    "이번",
    "오늘",
    "다시",
    "우리",
    "여러분",
    "정도",
    "생각",
    "사람",
    "대한민국",
    "대통령",
    "님",
    "이재명",
    "김혜경",
    "그냥",
    "거든요",
    "거네요",
    "같아요",
    "때문",
    "사실",
    "지금",
    "많이",
    "완전",
    "하다",
    "된다",
    "했다",
    "하는",
    "되는",
    "하고",
    "하면",
]

TOPIC_RULES: List[Tuple[str, List[str]]] = [
    ("정권 교체와 개혁 기대", ["정권", "개혁", "교체", "새정부", "변화", "바꾸", "개선"]),
    ("정부 비판과 정치 불신", ["비판", "불신", "무능", "부패", "정책", "실망"]),
    ("당선 축하와 사회 통합", ["축하", "응원", "감사", "희망", "화이팅", "미래"]),
    ("사법개혁과 책임 추궁", ["검찰", "법원", "개혁", "특검", "책임", "청산", "처벌"]),
    ("지역 갈등과 정치 분열", ["지역", "갈등", "대구", "경북", "전라", "분열"]),
    ("정책 논의와 생활 영향", ["정책", "경제", "복지", "세금", "물가", "일자리", "청년"]),
    ("정치 불안과 미래 우려", ["불안", "우려", "걱정", "위기", "미래", "망"]),
    ("외교 이슈와 국제 관계", ["외교", "중국", "미국", "북한", "국제", "관계"]),
]

EMOJI_INDICES = ["①", "②", "③"]


@dataclass
class Comment:
    idx: int
    raw: str
    clean: str


def normalize_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\u200b", " ")
    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_comments(lines: List[str]) -> List[Comment]:
    comments: List[Comment] = []
    buffer: List[str] = []
    current_idx: int | None = None

    for raw_line in lines[3:]:
        line = raw_line.strip()
        if match := re.match(r"^\[(\d+)\]\s*(.*)", line):
            if buffer and current_idx is not None:
                raw_comment = re.sub(r"<br\s*/?>", " ", " ".join(buffer).strip(), flags=re.I)
                raw_comment = re.sub(r"\s+", " ", raw_comment).strip()
                clean_comment = normalize_text(raw_comment)
                if clean_comment:
                    comments.append(Comment(current_idx, raw_comment, clean_comment))
            current_idx = int(match.group(1))
            first_line = match.group(2)
            buffer = [first_line] if first_line else []
        elif line:
            buffer.append(line)

    if buffer and current_idx is not None:
        raw_comment = re.sub(r"<br\s*/?>", " ", " ".join(buffer).strip(), flags=re.I)
        raw_comment = re.sub(r"\s+", " ", raw_comment).strip()
        clean_comment = normalize_text(raw_comment)
        if clean_comment:
            comments.append(Comment(current_idx, raw_comment, clean_comment))

    return comments


def prepare_comments(comments: List[Comment]) -> Tuple[List[Comment], Dict[str, List[str]]]:
    unique: Dict[str, Comment] = {}
    clean_to_raw: Dict[str, List[str]] = defaultdict(list)

    for comment in comments:
        if len(comment.clean) < 5:
            continue
        clean_to_raw[comment.clean].append(comment.raw)
        if comment.clean not in unique:
            unique[comment.clean] = comment

    return list(unique.values()), clean_to_raw


def select_topic_name(keywords: List[str], samples: List[str]) -> str:
    text = " ".join(keywords + samples).lower()
    best_name: str | None = None
    best_score = 0
    for name, triggers in TOPIC_RULES:
        score = sum(1 for trigger in triggers if trigger in text)
        if score > best_score:
            best_name = name
            best_score = score
    if best_name and best_score > 0:
        return best_name
    # 키워드 기반으로 일반적인 주제명 생성
    if keywords:
        # 특정 인물명이나 구체적 단어 제거
        generic_keywords = [k for k in keywords if len(k) > 2 and k not in ["윤석열", "이재명", "문재인", "김문수", "진짜", "너무", "그냥", "정말"]]
        if generic_keywords:
            # 키워드 의미를 해석해 주제명 생성
            for kw in generic_keywords:
                if any(t in kw for t in ["비판", "불신", "실망"]):
                    return "정부 비판과 정치 불신"
                if any(t in kw for t in ["축하", "응원", "감사", "희망"]):
                    return "당선 축하와 사회 통합"
                if any(t in kw for t in ["개혁", "교체", "변화"]):
                    return "정권 교체와 개혁 기대"
                if any(t in kw for t in ["정책", "경제", "복지", "세금"]):
                    return "정책 논의와 생활 영향"
                if any(t in kw for t in ["지역", "갈등", "분열"]):
                    return "지역 갈등과 정치 분열"
            return f"{generic_keywords[0]} 중심 정치 담론"
    return "주요 정치 담론"


def format_comment(raw: str) -> str:
    text = re.sub(r"\s+", " ", raw.strip())
    return text


def generate_topic_report(
    docs: List[Comment],
    topics: List[int],
    topic_model: BERTopic,
    clean_to_raw: Dict[str, List[str]],
    target_topics: int,
) -> str:
    topic_info = topic_model.get_topic_info()
    topic_info = topic_info[topic_info["Topic"] != -1]
    if topic_info.empty:
        return "추출된 주제가 없습니다."

    # 주제 수를 4-8개 사이로 제한
    topic_count = min(target_topics, max(4, min(8, len(topic_info))))
    topic_info = topic_info.head(topic_count)
    
    report_lines: List[str] = []

    topic_to_docs: Dict[int, List[str]] = defaultdict(list)
    for comment, topic_id in zip(docs, topics):
        topic_to_docs[topic_id].append(comment.clean)

    seen_topic_names: set[str] = set()
    order_counter = 1

    for _, row in topic_info.iterrows():
        topic_id = int(row["Topic"])
        keywords = [word for word, _ in (topic_model.get_topic(topic_id) or [])][:10]
        representative_docs = topic_model.get_representative_docs(topic_id)
        if not representative_docs:
            representative_docs = topic_to_docs.get(topic_id, [])

        raw_samples: List[str] = []
        seen: set[str] = set()
        for doc in representative_docs:
            for raw in clean_to_raw.get(doc, []):
                formatted = format_comment(raw)
                if formatted and formatted not in seen and len(formatted) > 10:
                    raw_samples.append(formatted)
                    seen.add(formatted)
                    break
            if len(raw_samples) >= 3:
                break

        if not raw_samples and representative_docs:
            fallback_raws = clean_to_raw.get(representative_docs[0], [])
            if fallback_raws:
                formatted = format_comment(fallback_raws[0])
                if formatted and len(formatted) > 10:
                    raw_samples.append(formatted)

        if not raw_samples:
            continue

        topic_name = select_topic_name(keywords, raw_samples)
        
        # 중복 주제 제거
        if topic_name in seen_topic_names:
            continue
        seen_topic_names.add(topic_name)

        report_lines.append(f"[주제 {order_counter}] {topic_name}")
        report_lines.append("대표 댓글:")
        for idx, comment_text in enumerate(raw_samples[:3]):
            marker = EMOJI_INDICES[idx] if idx < len(EMOJI_INDICES) else f"({idx + 1})"
            report_lines.append(f"  {marker} \"{comment_text}\"")
        report_lines.append("")
        
        order_counter += 1
        # 최대 8개까지만
        if len(seen_topic_names) >= 8:
            break

    return "\n".join(report_lines).strip()


def build_topic_model(comments: List[Comment], target_topics: int) -> Tuple[BERTopic, List[int]]:
    docs = [comment.clean for comment in comments]
    embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    n_clusters = max(target_topics, min(12, max(3, len(comments) // 400 + 4)))
    hdbscan_model = HDBSCAN(n_clusters=n_clusters, random_state=42)
    vectorizer_model = CountVectorizer(
        stop_words=STOP_WORDS,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[가-힣a-zA-Z]{2,}\b",
        max_features=20000,
    )

    topic_model = BERTopic(
        embedding_model=embedding_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        top_n_words=10,
        verbose=False,
        calculate_probabilities=False,
    )

    topics, _ = topic_model.fit_transform(docs)
    return topic_model, topics


def main() -> None:
    base_dir = Path(__file__).parent.parent.resolve()
    input_dir = base_dir / "extract_comments"

    if not input_dir.exists():
        print(f"❌ extract_comments 폴더를 찾을 수 없습니다: {input_dir}")
        sys.exit(1)

    txt_files = sorted(input_dir.glob("*.txt"))
    if not txt_files:
        print(f"❌ 분석할 txt 파일이 없습니다: {input_dir}")
        sys.exit(1)

    target_file = max(txt_files, key=lambda p: p.stat().st_mtime)
    print(f"분석 대상 파일: {target_file.name}")

    with target_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    parsed_comments = parse_comments(lines)
    prepared_comments, clean_to_raw = prepare_comments(parsed_comments)

    if len(prepared_comments) < 10:
        print("댓글 수가 너무 적어 주제 분석이 어렵습니다.")
        sys.exit(0)

    target_topics = 6
    topic_model, topics = build_topic_model(prepared_comments, target_topics)
    report = generate_topic_report(prepared_comments, topics, topic_model, clean_to_raw, target_topics)

    print(report)

    output_dir = base_dir / "comments_result"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{target_file.stem}_topics_{timestamp}.txt"
    output_path.write_text(report, encoding="utf-8")

    print()
    print(f"[저장 완료] 결과 파일: {output_path}")


if __name__ == "__main__":
    main()
