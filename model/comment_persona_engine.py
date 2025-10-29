"""
댓글 페르소나 엔진 (LLM 기반, CPU 경량 안정형)
댓글 수집 → LLM 기반 페르소나 생성
skt/kogpt2-base-v2 기반, CPU 전용, 메모리 안전 모드 + JSON 파싱 보강
"""

from typing import List, Dict, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch, json, re
from collections import Counter


class CommentPersonaEngine:
    """댓글 기반 페르소나 학습 엔진 (CPU 경량 버전)"""

    def __init__(self):
        # ---------------------------------------
        # 기본 상태 초기화
        # ---------------------------------------
        self.left_comments: List[str] = []
        self.right_comments: List[str] = []
        self.left_persona: Optional[Dict] = None
        self.right_persona: Optional[Dict] = None

        # ---------------------------------------
        # ✅ CPU 전용 경량 모델 설정
        # ---------------------------------------
        model_id = "skt/kogpt2-base-v2"  # ✅ 공개 + 경량 + 한국어 지원
        print(f"🚀 페르소나 생성 LLM 로딩 중: {model_id}...")

        self.device = "cpu"
        self.device_map = None
        self.dtype = torch.float32

        print(f"디바이스: {self.device.upper()} (경량 CPU 모드)")

        # ---------------------------------------
        # ✅ 모델 및 토크나이저 로드 (안전)
        # ---------------------------------------
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=self.dtype,
                device_map=self.device_map,
                low_cpu_mem_usage=True
            ).to(self.device)

            self.llm = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1  # ✅ CPU 강제
            )

            print("✓ 페르소나 생성 LLM 로딩 완료! (CPU 경량 모드)\n")

        except Exception as e:
            print(f"❌ 모델 로딩 실패: {e}")
            self.model, self.llm = None, None

    # ==========================================================
    # 댓글 수집
    # ==========================================================
    def add_left_comments(self, comments: List[str]):
        valid = [c.strip() for c in comments if c.strip()]
        self.left_comments.extend(valid)
        print(f"좌파 댓글 {len(valid)}개 추가 (총 {len(self.left_comments)}개)")

    def add_right_comments(self, comments: List[str]):
        valid = [c.strip() for c in comments if c.strip()]
        self.right_comments.extend(valid)
        print(f"우파 댓글 {len(valid)}개 추가 (총 {len(self.right_comments)}개)")

    # ==========================================================
    # LLM 기반 페르소나 생성
    # ==========================================================
    def generate_persona_via_llm(self, side: str) -> Optional[Dict]:
        comments = self.left_comments if side == "left" else self.right_comments
        if not comments or len(comments) < 5:
            print(f"[{side}] 댓글 부족: {len(comments)}개")
            return None

        side_name = '진보(좌파)' if side == 'left' else '보수(우파)'
        print(f"\n{'='*60}")
        print(f"🤖 {side_name} 페르소나 생성 시작... (댓글 {len(comments)}개)")
        print(f"{'='*60}\n")

        prompt = f"""다음은 {side_name} 성향의 정치 뉴스 댓글입니다.
말투, 감정, 가치관을 분석해 JSON으로 요약하세요.

댓글:
{chr(10).join(comments[:15])}

JSON 형식으로만, 다른 문장 없이 정확한 JSON만 출력하세요.
출력 예시:
{{
  "summary": "한 문장 요약",
  "values": ["핵심가치1", "핵심가치2"],
  "tone": ["말투특징1", "말투특징2"],
  "emotion": "감정스타일",
  "keywords": ["키워드1", "키워드2", "키워드3"],
  "quote_examples": ["예시1", "예시2"]
}}"""

        try:
            if not self.llm:
                raise RuntimeError("LLM이 초기화되지 않았습니다.")

            print("⏳ LLM 처리 중...")
            result = self.llm(
                prompt,
                max_new_tokens=300,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )[0]["generated_text"]

            json_start, json_end = result.find("{"), result.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                print("⚠ JSON 응답 없음 → 기본 페르소나 생성")
                persona = self._create_default_persona(side, comments)
            else:
                try:
                    json_str = result[json_start:json_end]
                    persona = json.loads(json_str)
                except json.JSONDecodeError:
                    # ⚙️ JSON 파싱 재시도 (} 이전까지만 잘라서)
                    clean_json = result[json_start:].split("}")[0] + "}"
                    try:
                        persona = json.loads(clean_json)
                        print("⚠ JSON 파싱 보정 성공")
                    except Exception:
                        print("⚠ JSON 파싱 재시도 실패 → 기본 페르소나 생성")
                        persona = self._create_default_persona(side, comments)

            print(f"✅ {side_name} 페르소나 생성 완료!")
            if side == "left":
                self.left_persona = persona
            else:
                self.right_persona = persona
            return persona

        except Exception as e:
            print(f"❌ 페르소나 생성 실패: {e}")
            return self._create_default_persona(side, comments)

    # ==========================================================
    # 기본 페르소나 생성 (LLM 실패 시)
    # ==========================================================
    def _create_default_persona(self, side: str, comments: List[str]) -> Dict:
        words = []
        for c in comments:
            words.extend(re.findall(r'[가-힣]+', c))
        top_keywords = [w for w, _ in Counter(words).most_common(10) if len(w) >= 2]
        side_name = "진보(좌파)" if side == "left" else "보수(우파)"
        return {
            "summary": f"{side_name} 성향의 기본 페르소나",
            "values": ["사회 정의", "변화"] if side == "left" else ["안정", "전통"],
            "tone": ["열정적", "직설적"] if side == "left" else ["냉정한", "논리적"],
            "emotion": "확신",
            "keywords": top_keywords[:8],
            "quote_examples": comments[:3]
        }

    # ==========================================================
    # 조회 / 상태 관련 유틸
    # ==========================================================
    def get_stats(self):
        return {
            "left_count": len(self.left_comments),
            "right_count": len(self.right_comments),
            "persona_ready": self.comments_ready(),
            "personas_generated": self.personas_generated(),
        }

    def comments_ready(self) -> bool:
        return len(self.left_comments) >= 5 and len(self.right_comments) >= 5

    def personas_generated(self) -> bool:
        return self.left_persona is not None and self.right_persona is not None

    def is_ready(self) -> bool:
        return self.comments_ready() and self.personas_generated()

    def get_persona(self, side: str) -> Optional[Dict]:
        return self.left_persona if side == "left" else self.right_persona

    def get_persona_prompt(self, side: str) -> str:
        persona = self.get_persona(side)
        side_name = "진보(좌파)" if side == "left" else "보수(우파)"
        if not persona:
            return f"당신은 {side_name} 성향의 한국 댓글러입니다."

        prompt = f"""당신은 {side_name} 성향의 한국 유튜브 댓글러입니다.

페르소나 특성:
- 요약: {persona.get('summary', 'N/A')}
- 핵심 가치: {', '.join(persona.get('values', []))}
- 말투: {', '.join(persona.get('tone', []))}
- 감정: {persona.get('emotion', 'N/A')}
- 자주 쓰는 키워드: {', '.join(persona.get('keywords', [])[:5])}

실제 댓글 예시:
{chr(10).join([f'- {ex}' for ex in persona.get('quote_examples', [])[:3]])}

위 패턴과 어투를 참고하여 자연스럽고 실감나는 댓글을 작성하세요."""
        return prompt

    def reset(self):
        self.left_comments, self.right_comments = [], []
        self.left_persona, self.right_persona = None, None
        print("모든 댓글 및 페르소나 초기화 완료")
