"""
토론 관리 서비스
토론 세션 시작, 메시지 생성, 상태 관리 등의 비즈니스 로직
keywords 기반 토론 지원
"""
from datetime import datetime
from typing import Optional, Dict, List
from ..core.state import AppState
from ..models import (
    DebateState, DebateMessage, Side, AnalysisResult, 
    Argument, EmotionalPattern
)
from ..ai_debater import DebaterManager
from ..config.settings import settings


class DebateService:
    """토론 관련 비즈니스 로직"""
    
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        self.persona_engine = app_state.persona_engine
    
    def start_debate(
        self, 
        initial_topic: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        summary_sentences: Optional[List[str]] = None
    ) -> Dict:
        """
        토론 세션 시작
        
        Args:
            initial_topic: 초기 토론 주제 (선택)
            keywords: 토론 키워드 리스트 (하위 호환성)
            summary_sentences: 영상 요약 문장 리스트 (youtube_full_pipeline에서 전달)
            
        Returns:
            Dict: 토론 시작 정보
            
        Raises:
            ValueError: 페르소나가 준비되지 않은 경우
        """
        if not self.persona_engine.is_ready():
            raise ValueError(
                "페르소나가 아직 준비되지 않았습니다. "
                "먼저 /api/comments/generate-persona 실행"
            )
        
        # summary_sentences 우선, 없으면 keywords 사용 (하위 호환성)
        debate_topic = summary_sentences or keywords or []
        
        # 더미 분석 정보로 토론자 초기화
        dummy_analysis = AnalysisResult(
            left_arguments=[Argument(point="진보", keywords=["개혁"])],
            right_arguments=[Argument(point="보수", keywords=["안정"])],
            controversial_keywords=debate_topic[:3] if debate_topic else ["정치"],
            left_emotional_patterns=[EmotionalPattern(pattern="열정적", examples=[])],
            right_emotional_patterns=[EmotionalPattern(pattern="냉정함", examples=[])],
            sample_comments={"left": [], "right": []}
        )
        
        # OpenAI API 키 가져오기
        openai_api_key = settings.openai_api_key
        openai_model = settings.openai_model
        
        # DebaterManager 생성 (summary_sentences 전달)
        self.app_state.debater_manager = DebaterManager(
            dummy_analysis, 
            self.persona_engine,
            openai_api_key=openai_api_key,
            model=openai_model,
            keywords=debate_topic  # summary_sentences를 keywords 파라미터로 전달
        )
        
        # 토론 초기 상태
        topic = initial_topic or settings.initial_topic
        if debate_topic:
            topic = f"{topic} (영상 요약 기반)"
        
        self.app_state.current_debate_state = DebateState(
            message_count=0,
            messages=[],
            current_topic=topic,
            topics_covered=[],
            is_active=True
        )
        
        return {
            "message": "토론 시작",
            "state": self.app_state.current_debate_state,
            "persona_ready": self.persona_engine.is_ready(),
            "summary_sentences": debate_topic
        }
    
    def generate_next_message(self, side: Optional[Side] = None) -> Dict:
        """
        다음 발언 생성 (좌/우 번갈아)
        
        Args:
            side: 발언할 성향 (None이면 자동으로 번갈아)
            
        Returns:
            Dict: 생성된 메시지와 업데이트된 상태
            
        Raises:
            ValueError: 토론이 시작되지 않은 경우
            RuntimeError: DebaterManager가 초기화되지 않은 경우
        """
        state = self.app_state.current_debate_state
        debater_manager = self.app_state.debater_manager
        
        if not state or not state.is_active:
            raise ValueError("토론이 아직 시작되지 않았습니다.")
        
        if not debater_manager:
            raise RuntimeError("DebaterManager가 초기화되지 않았습니다.")
        
        # 발언 순서 결정
        state.message_count += 1
        if side is None:
            side = Side.LEFT if state.message_count % 2 == 1 else Side.RIGHT
        
        # 상대방의 마지막 메시지 찾기
        opponent_side = Side.RIGHT if side == Side.LEFT else Side.LEFT
        opponent_message = None
        for msg in reversed(state.messages):
            if msg.side == opponent_side:
                opponent_message = msg
                break
        
        # 응답 생성
        side_name = '좌파' if side == Side.LEFT else '우파'
        print(f"{side_name} 응답 생성 중...")
        content = debater_manager.generate_response(side, state, opponent_message)
        print(f"응답 완료: {content[:50]}...")
        
        # 메시지 생성
        message = DebateMessage(
            side=side,
            content=content,
            current_topic=state.current_topic,
            timestamp=datetime.now().isoformat()
        )
        state.messages.append(message)
        
        return {
            "message": message,
            "state": state
        }
    
    def get_debate_status(self) -> Dict:
        """
        현재 토론 상태 조회
        
        Returns:
            Dict: 현재 토론 상태
            
        Raises:
            ValueError: 진행 중인 토론이 없는 경우
        """
        state = self.app_state.current_debate_state
        if not state:
            raise ValueError("진행 중인 토론이 없습니다.")
        
        return {"state": state}
    
    def reset_debate(self) -> Dict[str, str]:
        """
        토론 세션 초기화
        
        Returns:
            Dict: 초기화 완료 메시지
        """
        self.app_state.reset_debate()
        return {"message": "토론이 초기화되었습니다."}

