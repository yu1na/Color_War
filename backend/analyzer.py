"""
댓글 분석 엔진 (로컬 LLM 버전, CPU 경량 모델 사용)
jhgan/ko-alpaca-7b를 사용하여 감정 분석 및 성향 분류
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List
from models import AnalysisResult, Argument, EmotionalPattern


class CommentAnalyzer:
    """댓글 분석 엔진 (규칙 기반 + 선택적 LLM)"""

    def __init__(self, use_llm=False):
        """
        Args:
            use_llm: True면 LLM 사용, False면 규칙 기반 (빠름, 메모리 적게 사용)
        """
        self.use_llm = use_llm
        self.model = None
        self.tokenizer = None

        if use_llm:
            # ✅ 경량 한국어 모델 (CPU에서 빠르게 동작)
            self.model_name = "jhgan/ko-alpaca-7b"
            self.device = "cpu"

            print(f"⚙️ 감정 분석 LLM 모델 로딩 중: {self.model_name}")
            print(f"디바이스: {self.device.upper()} (경량 CPU 모드)")

            try:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    trust_remote_code=True
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,  # CPU 모드
                    device_map=None,
                    low_cpu_mem_usage=True,
                    trust_remote_code=True
                ).to(self.device)

                print("✓ 감정 분석 모델 로딩 완료 (경량 CPU 모드)")
            except Exception as e:
                print(f"⚠ 모델 로딩 실패: {e}")
                print("→ 규칙 기반 분석으로 자동 전환합니다.")
                self.model = None
                self.tokenizer = None
                self.use_llm = False
        else:
            print("✓ 규칙 기반 댓글 분석 사용 (빠름, 메모리 효율적)")

    # --------------------------------------------
    # 메인 분석 함수
    # --------------------------------------------
    def analyze_comments(self, comments_text: str) -> AnalysisResult:
        """댓글 텍스트를 분석하여 좌파/우파 논점을 추출"""
        comments = [c.strip() for c in comments_text.split('\n') if c.strip()]

        if not self.use_llm or not self.model or not self.tokenizer:
            return self._simple_analysis(comments)

        return self._llm_analysis(comments)

    # --------------------------------------------
    # LLM 기반 분석
    # --------------------------------------------
    def _llm_analysis(self, comments: List[str]) -> AnalysisResult:
        """LLM을 사용한 고급 분석"""
        prompt = self._create_analysis_prompt(comments[:30])  # 최대 30개만 사용

        try:
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=2048,
                truncation=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,  # ✅ 토큰 수 줄여 속도 개선
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = generated[len(prompt):].strip()

            return self._parse_llm_response(response, comments)

        except Exception as e:
            print(f"⚠ LLM 분석 오류: {e}")
            return self._simple_analysis(comments)

    # --------------------------------------------
    # 프롬프트 생성
    # --------------------------------------------
    def _create_analysis_prompt(self, comments: List[str]) -> str:
        comments_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(comments)])
        return f"""다음은 정치 관련 댓글들입니다. 이 댓글들을 분석하여 좌파(진보)와 우파(보수)의 주요 논점을 파악해주세요.

댓글:
{comments_str}

다음 형식으로 분석 결과를 작성해주세요:

[좌파 논점]
1. 
2. 
3. 

[우파 논점]
1. 
2. 
3. 

[논쟁 키워드]
키워드1, 키워드2, 키워드3

분석:"""

    # --------------------------------------------
    # LLM 응답 파싱
    # --------------------------------------------
    def _parse_llm_response(self, response: str, original_comments: List[str]) -> AnalysisResult:
        left_args, right_args, keywords = [], [], []
        lines = response.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if '[좌파 논점]' in line or '좌파' in line:
                current_section = 'left'
            elif '[우파 논점]' in line or '우파' in line:
                current_section = 'right'
            elif '[논쟁 키워드]' in line or '키워드' in line:
                current_section = 'keywords'
            elif line and current_section:
                if current_section == 'left' and (line[0].isdigit() or line.startswith('-')):
                    content = line.lstrip('0123456789.-) ').strip()
                    if content:
                        left_args.append(Argument(point=content, keywords=[]))
                elif current_section == 'right' and (line[0].isdigit() or line.startswith('-')):
                    content = line.lstrip('0123456789.-) ').strip()
                    if content:
                        right_args.append(Argument(point=content, keywords=[]))
                elif current_section == 'keywords':
                    keywords.extend([k.strip() for k in line.split(',') if k.strip()])

        # 최소 보장값
        if not left_args:
            left_args = [Argument(point="진보적 개혁 필요", keywords=["개혁", "진보"])]
        if not right_args:
            right_args = [Argument(point="안정적 보수 유지", keywords=["안정", "보수"])]
        if not keywords:
            keywords = ["정치", "정책", "정부"]

        # 샘플 댓글
        left_samples, right_samples = [], []
        for c in original_comments[:20]:
            if any(w in c for w in ['진보', '민주', '개혁']):
                left_samples.append(c)
            elif any(w in c for w in ['보수', '전통', '우파']):
                right_samples.append(c)

        return AnalysisResult(
            left_arguments=left_args[:5],
            right_arguments=right_args[:5],
            controversial_keywords=keywords[:15],
            left_emotional_patterns=[
                EmotionalPattern(pattern="진보적 표현", examples=left_samples[:3])
            ],
            right_emotional_patterns=[
                EmotionalPattern(pattern="보수적 표현", examples=right_samples[:3])
            ],
            sample_comments={
                "left": left_samples[:5],
                "right": right_samples[:5]
            }
        )

    # --------------------------------------------
    # 규칙 기반 폴백 분석
    # --------------------------------------------
    def _simple_analysis(self, comments: List[str]) -> AnalysisResult:
        """간단한 키워드 기반 분석 (폴백)"""
        left_keywords = ['진보', '개혁', '민주', '평등', '복지', '인권', '환경']
        right_keywords = ['보수', '전통', '안보', '경제', '성장', '질서', '안정']

        left_comments, right_comments, all_keywords = [], [], set()

        for comment in comments:
            words = comment.split()
            for w in words:
                if len(w) >= 2:
                    all_keywords.add(w)
            if any(k in comment for k in left_keywords):
                left_comments.append(comment)
            elif any(k in comment for k in right_keywords):
                right_comments.append(comment)
            else:
                (left_comments if len(left_comments) <= len(right_comments) else right_comments).append(comment)

        return AnalysisResult(
            left_arguments=[
                Argument(point="진보적 개혁 주장", keywords=left_keywords[:3]),
                Argument(point="사회 평등 강조", keywords=["평등", "복지"]),
                Argument(point="민주적 가치 추구", keywords=["민주", "인권"])
            ],
            right_arguments=[
                Argument(point="보수적 안정 추구", keywords=right_keywords[:3]),
                Argument(point="경제 성장 중시", keywords=["경제", "성장"]),
                Argument(point="전통 질서 유지", keywords=["전통", "질서"])
            ],
            controversial_keywords=list(all_keywords)[:20],
            left_emotional_patterns=[
                EmotionalPattern(pattern="진보적 어조", examples=left_comments[:3])
            ],
            right_emotional_patterns=[
                EmotionalPattern(pattern="보수적 어조", examples=right_comments[:3])
            ],
            sample_comments={
                "left": left_comments[:10],
                "right": right_comments[:10]
            }
        )
