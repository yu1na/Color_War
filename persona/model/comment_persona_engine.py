"""
댓글 페르소나 엔진 (OpenAI GPT-4o-mini 기반)
댓글 수집 → OpenAI 기반 페르소나 생성
좌/우 각 5개 댓글 샘플링하여 학습
"""

from typing import List, Dict, Optional
import json
import random
import os


class CommentPersonaEngine:
    """댓글 기반 페르소나 학습 엔진 (OpenAI 기반)"""

    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Args:
            openai_api_key: OpenAI API 키
            model: 사용할 OpenAI 모델 (기본값: gpt-4o-mini)
        """
        # OpenAI 클라이언트 초기화
        try:
            from openai import OpenAI
            
            # API 키 설정 (환경변수 또는 인자)
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API 키가 설정되지 않았습니다. OPENAI_API_KEY 환경변수를 설정하거나 인자로 전달하세요.")
            
            self.client = OpenAI(api_key=api_key)
            self.model = model
            print(f"✅ OpenAI 클라이언트 초기화 완료 (모델: {model})")
            
        except ImportError:
            raise ImportError("openai 패키지가 설치되지 않았습니다. 'pip install openai'를 실행하세요.")
        except Exception as e:
            raise RuntimeError(f"OpenAI 클라이언트 초기화 실패: {e}")

        # 댓글 저장소
        self.left_comments: List[str] = []
        self.right_comments: List[str] = []
        
        # 생성된 페르소나
        self.left_persona: Optional[Dict] = None
        self.right_persona: Optional[Dict] = None

    # ==========================================================
    # 댓글 수집
    # ==========================================================
    def add_left_comments(self, comments: List[str]):
        """좌파 댓글 추가"""
        valid = [c.strip() for c in comments if c.strip()]
        self.left_comments.extend(valid)
        print(f"좌파 댓글 {len(valid)}개 추가 (총 {len(self.left_comments)}개)")

    def add_right_comments(self, comments: List[str]):
        """우파 댓글 추가"""
        valid = [c.strip() for c in comments if c.strip()]
        self.right_comments.extend(valid)
        print(f"우파 댓글 {len(valid)}개 추가 (총 {len(self.right_comments)}개)")

    # ==========================================================
    # OpenAI 기반 페르소나 생성 (5개 샘플링)
    # ==========================================================
    def generate_persona_via_llm(self, side: str) -> Optional[Dict]:
        """
        OpenAI를 사용하여 페르소나 생성
        
        Args:
            side: "left" 또는 "right"
            
        Returns:
            생성된 페르소나 딕셔너리 또는 None
        """
        comments = self.left_comments if side == "left" else self.right_comments
        
        if not comments or len(comments) < 5:
            print(f"[{side}] 댓글 부족: {len(comments)}개 (최소 5개 필요)")
            return None

        side_name = '진보(좌파)' if side == 'left' else '보수(우파)'
        print(f"\n{'='*60}")
        print(f"🤖 {side_name} 페르소나 생성 시작... (전체 댓글: {len(comments)}개)")
        print(f"{'='*60}\n")

        # Structure에서 이미 5개를 전달받았으면 그대로 사용, 아니면 랜덤 샘플링
        if len(comments) == 5:
            sampled_comments = comments
            print(f"📝 Structure에서 전달받은 댓글 5개 사용:")
        else:
            sampled_comments = random.sample(comments, min(5, len(comments)))
            print(f"📝 랜덤 샘플링된 댓글 {len(sampled_comments)}개:")
        
        for i, comment in enumerate(sampled_comments, 1):
            print(f"  {i}. {comment[:50]}...")

        # OpenAI 프롬프트 구성
        prompt = f"""다음은 {side_name} 성향의 유튜브 정치 댓글 5개입니다.
이 댓글들의 말투, 감정, 가치관, 논조를 분석하여 페르소나를 생성하세요.

댓글:
{chr(10).join([f"{i+1}. {c}" for i, c in enumerate(sampled_comments)])}

위 댓글들을 분석하여 다음 JSON 형식으로만 응답하세요. 다른 설명은 포함하지 마세요:

{{
  "summary": "이 페르소나의 특징을 한 문장으로 요약",
  "values": ["핵심가치1", "핵심가치2", "핵심가치3"],
  "tone": ["말투특징1", "말투특징2"],
  "emotion": "주요 감정 스타일",
  "keywords": ["자주 쓰는 키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
  "quote_examples": ["대표 표현1", "대표 표현2", "대표 표현3"]
}}"""

        try:
            print("⏳ OpenAI API 호출 중...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 한국 정치 댓글을 분석하는 전문가입니다. JSON 형식으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            result = response.choices[0].message.content.strip()
            print(f"📥 OpenAI 응답 수신 완료")
            
            # JSON 파싱
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                print("⚠️ JSON 형식을 찾을 수 없음 → 기본 페르소나 생성")
                persona = self._create_default_persona(side, sampled_comments)
            else:
                json_str = result[json_start:json_end]
                try:
                    persona = json.loads(json_str)
                    print(f"✅ {side_name} 페르소나 생성 완료!")
                    print(f"   요약: {persona.get('summary', 'N/A')}")
                    print(f"   키워드: {', '.join(persona.get('keywords', [])[:5])}")
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON 파싱 실패: {e} → 기본 페르소나 생성")
                    persona = self._create_default_persona(side, sampled_comments)

            # 페르소나 저장
            if side == "left":
                self.left_persona = persona
            else:
                self.right_persona = persona
                
            return persona

        except Exception as e:
            print(f"❌ 페르소나 생성 실패: {e}")
            return self._create_default_persona(side, sampled_comments)

    # ==========================================================
    # 기본 페르소나 생성 (OpenAI 실패 시 폴백)
    # ==========================================================
    def _create_default_persona(self, side: str, comments: List[str]) -> Dict:
        """OpenAI 호출 실패 시 사용할 기본 페르소나"""
        side_name = "진보(좌파)" if side == "left" else "보수(우파)"
        
        # 댓글에서 자주 등장하는 단어 추출 (간단한 방법)
        import re
        from collections import Counter
        
        words = []
        for c in comments:
            words.extend(re.findall(r'[가-힣]+', c))
        top_keywords = [w for w, _ in Counter(words).most_common(10) if len(w) >= 2]
        
        return {
            "summary": f"{side_name} 성향의 기본 페르소나 (OpenAI 미사용)",
            "values": ["사회 정의", "평등", "변화"] if side == "left" else ["안정", "전통", "질서"],
            "tone": ["열정적", "직설적", "감성적"] if side == "left" else ["냉정한", "논리적", "원칙적"],
            "emotion": "분노와 열정" if side == "left" else "냉정과 확신",
            "keywords": top_keywords[:5] if top_keywords else ["정치", "정부", "국민", "사회", "문제"],
            "quote_examples": comments[:3]
        }

    # ==========================================================
    # 조회 / 상태 관련 유틸
    # ==========================================================
    def get_stats(self):
        """현재 상태 통계"""
        return {
            "left_count": len(self.left_comments),
            "right_count": len(self.right_comments),
            "persona_ready": self.comments_ready(),
            "personas_generated": self.personas_generated(),
        }

    def comments_ready(self) -> bool:
        """댓글이 충분히 수집되었는지 확인 (각 5개 이상)"""
        return len(self.left_comments) >= 5 and len(self.right_comments) >= 5

    def personas_generated(self) -> bool:
        """페르소나가 생성되었는지 확인"""
        return self.left_persona is not None and self.right_persona is not None

    def is_ready(self) -> bool:
        """페르소나 시스템이 준비되었는지 확인"""
        return self.comments_ready() and self.personas_generated()

    def get_persona(self, side: str) -> Optional[Dict]:
        """특정 성향의 페르소나 조회"""
        return self.left_persona if side == "left" else self.right_persona

    def get_persona_prompt(self, side: str) -> str:
        """
        토론에 사용할 페르소나 프롬프트 생성
        
        Args:
            side: "left" 또는 "right"
            
        Returns:
            페르소나를 설명하는 프롬프트 문자열
        """
        persona = self.get_persona(side)
        side_name = "진보(좌파)" if side == "left" else "보수(우파)"
        
        if not persona:
            return f"당신은 {side_name} 성향의 한국 유튜브 댓글러입니다."

        prompt = f"""당신은 {side_name} 성향의 한국 유튜브 댓글러입니다.

페르소나 특성:
- 요약: {persona.get('summary', 'N/A')}
- 핵심 가치: {', '.join(persona.get('values', []))}
- 말투: {', '.join(persona.get('tone', []))}
- 감정: {persona.get('emotion', 'N/A')}
- 자주 쓰는 키워드: {', '.join(persona.get('keywords', [])[:5])}

실제 댓글 예시:
{chr(10).join([f'- {ex}' for ex in persona.get('quote_examples', [])[:3]])}

위 페르소나를 바탕으로 자연스럽고 실감나는 댓글을 작성하세요.
이전 대화 내용을 참고하되, 같은 표현을 반복하지 마세요."""
        
        return prompt

    def reset(self):
        """모든 댓글 및 페르소나 초기화"""
        self.left_comments, self.right_comments = [], []
        self.left_persona, self.right_persona = None, None
        print("✅ 모든 댓글 및 페르소나 초기화 완료")
