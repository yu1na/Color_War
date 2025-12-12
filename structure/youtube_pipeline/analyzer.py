from typing import List, Dict, Any
import re
import math
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (최상위 .env만 사용)
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
try:
    loaded = load_dotenv(ROOT_ENV, override=True)
    print(f"[dotenv] loaded(root-only): {ROOT_ENV} exists={ROOT_ENV.exists()} loaded={loaded}")
except Exception as e:
    print(f"[dotenv] load error: {e}")

def _softmax(a: float, b: float) -> (float, float):
    ma = max(a, b)
    ea, eb = math.exp(a - ma), math.exp(b - ma)
    s = ea + eb
    return ea / s, eb / s

def _normalize(text: str) -> str:
    t = re.sub(r"<br\s*/?>", " ", text)
    t = re.sub(r"[^\w\u3131-\u318E\uAC00-\uD7A3\s!?~]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower()

NEGATIONS = {"아니다", "아닌", "안", "못", "거짓", "허위", "no", "not"}

# 2025 이슈 반영 확장 키워드
LEFT_FRAMES = {
    "이재명", "민주당", "언론개혁", "검찰개혁", "복지", "노동", "전공의 무시", "의료붕괴",
    "특검 필요", "외교 무능", "임대차 보호", "투기 억제", "노동권", "대화", "평화", "협력",
    "환경", "인권", "재분배", "서민", "청년", "플랫폼노동", "젠더 평등", "소수자"
}
RIGHT_FRAMES = {
    "윤석열", "국민의힘", "법치", "안보", "시장", "기업", "규제완화", "공급 확대", "재건축 완화",
    "공공의료 강화", "의사기득권", "불법파업", "강경 대응", "확성기", "동맹", "군사력",
    "친중", "공산화", "부정선거", "범죄자", "검찰 정상화", "질서", "효율", "책임", "전통", "가정"
}

POS_EMO = {"축하", "만세", "고맙", "감사", "사랑"}
NEG_EMO = {"망했", "실패", "지옥", "분노", "혐오", "싫다"}
EMOJI_POS = {"❤", "💙", "💗", "💟", "🥰", "👏"}
EMOJI_NEG = {"💀", "🤮", "😡", "👎"}

def extract_features(text: str) -> Dict[str, Any]:
    t = _normalize(text)
    feats = {"left": 0.0, "right": 0.0, "hits": []}

    # 이슈별 좌/우 프레임 감지
    for word in LEFT_FRAMES:
        if word in t:
            feats["left"] += 1.0
            feats["hits"].append(f"L:{word}")
    for word in RIGHT_FRAMES:
        if word in t:
            feats["right"] += 1.0
            feats["hits"].append(f"R:{word}")

    # 감정/이모지 방향성
    if any(k in t for k in POS_EMO) or any(ch in text for ch in EMOJI_POS):
        if any(k in t for k in ["이재명", "민주", "복지", "노동"]):
            feats["left"] += 0.8; feats["hits"].append("긍정→좌파")
        if any(k in t for k in ["윤석열", "국힘", "시장", "법치"]):
            feats["right"] += 0.8; feats["hits"].append("긍정→우파")
    if any(k in t for k in NEG_EMO) or any(ch in text for ch in EMOJI_NEG):
        if any(k in t for k in ["이재명", "민주"]):
            feats["right"] += 0.6; feats["hits"].append("부정→좌파비판")
        if any(k in t for k in ["윤석열", "국힘"]):
            feats["left"] += 0.6; feats["hits"].append("부정→우파비판")

    # 단어 카운트 기반 확률
    left_prob, right_prob = _softmax(feats["left"], feats["right"])
    label = "좌파" if left_prob > right_prob else "우파"
    confidence = round(max(left_prob, right_prob), 3)
    
    # 극단성 점수: 각 진영의 순수 점수 차이 (좌파면 left-right, 우파면 right-left)
    extremity_score = feats["left"] - feats["right"] if label == "좌파" else feats["right"] - feats["left"]

    return {
        "label": label, 
        "confidence": confidence, 
        "hits": feats["hits"],
        "left_score": feats["left"],
        "right_score": feats["right"],
        "extremity_score": extremity_score  # 극단성 점수
    }

class Analyzer:
    """댓글 분석 및 정치 성향 분류 Analyzer (OpenAI API 사용)"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. 키워드 기반 분류를 사용합니다.")
        else:
            print("✓ OpenAI API 키 확인 완료")
        
        # OpenAI 클라이언트 초기화 (API 키가 있을 때만)
        self.openai_client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.api_key)
                print("✓ OpenAI 클라이언트 초기화 완료")
            except ImportError:
                print("⚠️ openai 패키지가 설치되지 않았습니다. 'pip install openai' 실행 필요")
                self.api_key = None

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        s1, s2 = set(text1.lower().split()), set(text2.lower().split())
        if not s1 or not s2: return 0.0
        return len(s1 & s2) / len(s1 | s2)

    def filter_comments_by_similarity(self, comments: List[str], summary_sentences: List[str], max_comments: int = 500) -> List[Dict]:
        summary_text = " ".join(summary_sentences)
        objs = []
        for i, text in enumerate(comments):
            sim = self.calculate_similarity(text, summary_text)
            objs.append({"id": f"yt_{i}", "text": text, "similarity_score": sim, "author": f"사용자{i+1}"})
        objs.sort(key=lambda x: x["similarity_score"], reverse=True)
        return objs[:max_comments]

    def _classify_with_openai(self, comment_text: str) -> Dict[str, Any]:
        """OpenAI API를 사용하여 댓글 분류"""
        if not self.openai_client:
            # OpenAI를 사용할 수 없으면 키워드 기반으로 폴백
            return classify_primary(comment_text)
        
        system_prompt = """당신은 대한민국 정치 댓글의 정치 성향을 분석하는 전문가입니다.
주어진 댓글을 분석하여 좌파 또는 우파로 분류하세요.

좌파 특징: 이재명, 민주당 지지, 복지 확대, 노동권, 검찰개혁, 언론개혁, 대화/평화 외교
우파 특징: 윤석열, 국민의힘 지지, 시장경제, 법치, 안보 우선, 강경 대응, 동맹 강화

응답 형식: JSON으로 {"label": "좌파" 또는 "우파", "confidence": 0.0~1.0, "reasoning": "간단한 이유"}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 또는 "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"댓글: {comment_text}"}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSON 파싱 시도
            import json
            try:
                result = json.loads(result_text)
                label = result.get("label", "판단불가")
                confidence = float(result.get("confidence", 0.5))
                reasoning = result.get("reasoning", "")
                
                if label not in ("좌파", "우파"):
                    label = "판단불가"
                
                return {
                    "label": label,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "left_prob": confidence if label == "좌파" else 1 - confidence,
                    "right_prob": confidence if label == "우파" else 1 - confidence,
                    "features": {"method": "openai", "reasoning": reasoning}
                }
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트에서 추출
                if "좌파" in result_text:
                    return {"label": "좌파", "confidence": 0.7, "left_prob": 0.7, "right_prob": 0.3, 
                           "features": {"method": "openai", "raw": result_text}}
                elif "우파" in result_text:
                    return {"label": "우파", "confidence": 0.7, "left_prob": 0.3, "right_prob": 0.7,
                           "features": {"method": "openai", "raw": result_text}}
                else:
                    # 실패 시 키워드 기반으로 폴백
                    return classify_primary(comment_text)
        except Exception as e:
            print(f"⚠️ OpenAI API 오류: {e} - 키워드 기반으로 폴백")
            return classify_primary(comment_text)

    def _primary_pass(self, items: List[Dict]) -> List[Dict]:
        """1차 분류: OpenAI API 또는 키워드 기반"""
        enriched = []
        for obj in items:
            if self.openai_client:
                res = self._classify_with_openai(obj["text"])
            else:
                res = classify_primary(obj["text"])
            
            obj["political_orientation"] = res["label"] if res["label"] in ("좌파", "우파") else "판단불가"
            obj["classification_confidence"] = res["confidence"]
            obj["left_prob"] = res["left_prob"]
            obj["right_prob"] = res["right_prob"]
            obj["features"] = res.get("features", res)
            enriched.append(obj)
        return enriched

    def analyze_comments(self, comments: List[str], summary_sentences: List[str], top_k: int = 5) -> Dict[str, Any]:
        """
        summaries 기반으로 댓글 분석 후 극좌/극우 댓글 각 top_k개만 추출
        
        Args:
            comments: 전체 댓글 리스트
            summary_sentences: 영상 요약 문장 리스트
            top_k: 좌파/우파 각각 추출할 극단 댓글 개수 (기본 5개)
        """
        filtered = self.filter_comments_by_similarity(comments, summary_sentences, max_comments=500)
        if not filtered:
            return {'comments': [], 'statistics': {}, 'left_comments': [], 'right_comments': [], 'similarity_stats': {}}

        # 1차 분류
        analyzed = self._primary_pass(filtered)
        
        # 확신도 0.55 미만 제외 및 좌/우만 남김
        analyzed = [c for c in analyzed if c.get('classification_confidence', 0) >= 0.55 
                    and c.get('political_orientation') in ('좌파', '우파')]

        # 좌파/우파 분리
        left_comments = [c for c in analyzed if c.get('political_orientation') == '좌파']
        right_comments = [c for c in analyzed if c.get('political_orientation') == '우파']

        # 극단성 점수 계산: confidence 기반 또는 features의 left/right 점수 차이
        for c in left_comments:
            feats = c.get('features', {})
            if 'left' in feats and 'right' in feats:
                c['extremity_score'] = feats.get('left', 0) - feats.get('right', 0)
            else:
                # OpenAI 분류인 경우 confidence를 극단성 점수로 사용
                c['extremity_score'] = c.get('classification_confidence', 0.5)
        for c in right_comments:
            feats = c.get('features', {})
            if 'left' in feats and 'right' in feats:
                c['extremity_score'] = feats.get('right', 0) - feats.get('left', 0)
            else:
                # OpenAI 분류인 경우 confidence를 극단성 점수로 사용
                c['extremity_score'] = c.get('classification_confidence', 0.5)

        # 극단성 점수 기준으로 정렬 (높은 순)
        left_comments.sort(key=lambda x: x.get('extremity_score', 0), reverse=True)
        right_comments.sort(key=lambda x: x.get('extremity_score', 0), reverse=True)

        # 상위 top_k개만 선택
        top_left = left_comments[:top_k]
        top_right = right_comments[:top_k]
        
        # 최종 선택된 댓글들만 반환
        final = top_left + top_right

        stats = {"좌파": len(top_left), "우파": len(top_right)}
        total = len(final) or 1
        stats = {k: {"count": v, "percentage": round(v/total*100, 1)} for k, v in stats.items()}

        return {
            'comments': final,
            'statistics': stats,
            'left_comments': [c['text'] for c in top_left],
            'right_comments': [c['text'] for c in top_right],
            'similarity_stats': {}
        }
