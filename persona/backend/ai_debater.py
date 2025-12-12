"""
AI 토론자 시스템 (OpenAI GPT-4o-mini 기반)
페르소나를 반영하여 keywords 기반으로 토론 생성
중복 방지 로직 포함
"""

import os
from typing import Optional, List
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from model.comment_persona_engine import CommentPersonaEngine
from .models import Side, DebateMessage, AnalysisResult, DebateState


class AIDebater:
    """AI 토론자 (OpenAI 기반)"""

    def __init__(
        self, 
        side: Side, 
        analysis: AnalysisResult, 
        persona_engine: CommentPersonaEngine,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        keywords: Optional[List[str]] = None
    ):
        """
        Args:
            side: 토론자의 정치 성향 (LEFT/RIGHT)
            analysis: 댓글 분석 결과
            persona_engine: 페르소나 엔진
            openai_api_key: OpenAI API 키
            model: OpenAI 모델명
            keywords: 토론 주제 키워드 리스트
        """
        self.side = side
        self.analysis = analysis
        self.persona_engine = persona_engine
        self.keywords = keywords or []
        
        # OpenAI 클라이언트 초기화
        try:
            from openai import OpenAI
            
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
            
            self.client = OpenAI(api_key=api_key)
            self.model = model
            
        except ImportError:
            raise ImportError("openai 패키지가 설치되지 않았습니다. 'pip install openai'를 실행하세요.")
        except Exception as e:
            raise RuntimeError(f"OpenAI 클라이언트 초기화 실패: {e}")

        # 중복 방지를 위한 이전 응답 저장
        self.previous_responses: List[str] = []

    def generate_response(
        self, 
        state: DebateState, 
        opponent_message: Optional[DebateMessage] = None
    ) -> str:
        """
        토론 응답 생성 (OpenAI 기반, 중복 방지)
        
        Args:
            state: 현재 토론 상태
            opponent_message: 상대방의 마지막 메시지
            
        Returns:
            생성된 응답 문자열
        """
        side_str = "left" if self.side == Side.LEFT else "right"
        side_name = "진보(좌파)" if self.side == Side.LEFT else "보수(우파)"
        
        # 페르소나 프롬프트 가져오기
        persona_prompt = self.persona_engine.get_persona_prompt(side_str)

        # 최근 대화 내역 구성 (최대 6개)
        conversation_history = ""
        for msg in state.messages[-6:]:
            speaker = "나" if msg.side == self.side else "상대"
            conversation_history += f"{speaker}: {msg.content}\n"

        # 상대방 메시지
        opponent_text = opponent_message.content if opponent_message else "이 주제에 대해 당신의 의견을 말해주세요."

        # 토론 주제 (summary_sentences) 구성
        topic_summary = "\n".join(self.keywords) if self.keywords else "정치, 사회"

        # 이전 응답들 (중복 방지용)
        previous_responses_str = ""
        if self.previous_responses:
            recent_responses = self.previous_responses[-5:]  # 최근 5개만
            previous_responses_str = "\n".join([f"- {resp[:100]}..." for resp in recent_responses])

        # 시스템 프롬프트
        system_prompt = f"""{persona_prompt}

중요 규칙:
1. 이전에 했던 말을 반복하지 마세요.
2. 새로운 관점이나 논거를 제시하세요.
3. 한국어로 자연스럽게 작성하세요.
4. 댓글 스타일로 간결하게 작성하세요 (1문장).
5. 상대방을 비난하세요
6. 실제 사람처럼 해줘
7. ㅋㅋ 같은 인터넷 말투 같은것도 사용해줘 
8. 공격적으로 자주 욕도 하고 강한 주장을 펼치세요."""

        # 사용자 프롬프트
        user_prompt = f"""현재 토론 주제 (영상 요약):
{topic_summary}

최근 대화:
{conversation_history}

상대방: {opponent_text}

당신의 응답을 작성하세요. 다음 사항을 반드시 지켜주세요:
- 이전에 했던 다음 표현들을 반복하지 마세요:
{previous_responses_str if previous_responses_str else "(첫 발언입니다)"}

- 위 영상 요약 내용과 관련된 새로운 논점을 제시하세요.
- 2-3문장으로 간결하게 작성하세요.
- 유튜브 댓글 스타일로 자연스럽게 작성하세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.9,  # 다양성을 위해 높은 temperature
                max_tokens=100,
                presence_penalty=0.6,  # 반복 억제
                frequency_penalty=0.6   # 반복 억제
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            # 생성된 응답이 너무 길면 자르기
            if len(generated_text) > 60:
                sentences = generated_text.split('.')
                generated_text = '.'.join(sentences[:3]) + '.'
            
            # 이전 응답에 추가 (중복 방지용)
            self.previous_responses.append(generated_text)
            
            # 너무 많이 쌓이면 오래된 것 제거
            if len(self.previous_responses) > 20:
                self.previous_responses = self.previous_responses[-20:]
            
            return generated_text or f"{side_name}의 입장에서 더 생각해볼 필요가 있겠네요."

        except Exception as e:
            print(f"⚠️ {side_name} 응답 생성 실패: {e}")
            return f"음... 이 부분은 좀 더 생각해봐야겠어요. ({side_name})"


class DebaterManager:
    """토론자 관리 (OpenAI 기반)"""

    def __init__(
        self, 
        analysis: AnalysisResult, 
        persona_engine: CommentPersonaEngine,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        keywords: Optional[List[str]] = None
    ):
        """
        Args:
            analysis: 댓글 분석 결과
            persona_engine: 페르소나 엔진
            openai_api_key: OpenAI API 키
            model: OpenAI 모델명
            keywords: 토론 주제 키워드 리스트
        """
        self.analysis = analysis
        self.persona_engine = persona_engine
        self.keywords = keywords or []
        
        print(f"\n{'='*60}")
        print(f"🤖 AI 토론자 초기화 중... (모델: {model})")
        print(f"{'='*60}")
        print(f"\n🎯 토론 주제:")
        if self.keywords:
            # 1문장 주제면 크게 출력
            if len(self.keywords) == 1:
                print(f"\n   💬 \"{self.keywords[0]}\"\n")
            else:
                for i, sentence in enumerate(self.keywords, 1):
                    print(f"   {i}. {sentence}")
        else:
            print("   (주제 없음)")
        print(f"{'='*60}\n")

        # 좌파/우파 토론자 생성
        self.left_debater = AIDebater(
            Side.LEFT, 
            analysis, 
            persona_engine,
            openai_api_key,
            model,
            keywords
        )
        
        self.right_debater = AIDebater(
            Side.RIGHT, 
            analysis, 
            persona_engine,
            openai_api_key,
            model,
            keywords
        )
        
        print("✅ AI 토론자 초기화 완료!\n")

    def generate_response(
        self, 
        side: Side, 
        state: DebateState, 
        opponent_message: Optional[DebateMessage] = None
    ) -> str:
        """
        특정 성향의 토론자 응답 생성
        
        Args:
            side: 응답할 토론자의 성향
            state: 현재 토론 상태
            opponent_message: 상대방의 마지막 메시지
            
        Returns:
            생성된 응답 문자열
        """
        if side == Side.LEFT:
            return self.left_debater.generate_response(state, opponent_message)
        else:
            return self.right_debater.generate_response(state, opponent_message)
