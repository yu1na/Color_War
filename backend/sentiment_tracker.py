"""
감정 추적 및 주제 전환 시스템
토론 진행에 따라 감정 레벨을 추적하고 주제를 자동으로 전환합니다.
"""
import random
from typing import List, Optional
from models import DebateState, DebateMessage, Side, AnalysisResult


class SentimentTracker:
    """감정 추적 및 주제 전환 관리 클래스"""
    
    def __init__(self, analysis: AnalysisResult):
        self.analysis = analysis
        self.base_escalation_rate = 0.5  # 기본 감정 상승률
        self.controversial_keywords = analysis.controversial_keywords
        self.available_topics = self._extract_topics()
    
    def _extract_topics(self) -> List[str]:
        """분석 결과에서 토론 주제들을 추출"""
        topics = []
        
        # 좌파 논점에서 주제 추출
        for arg in self.analysis.left_arguments[:3]:
            if arg.keywords:
                topics.append(arg.keywords[0])
        
        # 우파 논점에서 주제 추출
        for arg in self.analysis.right_arguments[:3]:
            if arg.keywords:
                topics.append(arg.keywords[0])
        
        # 논쟁적 키워드 추가
        topics.extend(self.controversial_keywords[:5])
        
        return list(set(topics))  # 중복 제거
    
    
    def should_change_topic(self, state: DebateState) -> bool:
        """
        주제를 전환해야 하는지 판단합니다.
        
        Args:
            state: 현재 토론 상태
            
        Returns:
            bool: 주제 전환 필요 여부
        """
        # 8-12개 메시지마다 랜덤하게 주제 전환
        if state.message_count > 0 and state.message_count % random.randint(8, 12) == 0:
            return True
        
        return False
    
    def get_next_topic(self, state: DebateState) -> str:
        """
        다음 토론 주제를 선택합니다.
        
        Args:
            state: 현재 토론 상태
            
        Returns:
            str: 새로운 주제
        """
        # 아직 다루지 않은 주제들
        unused_topics = [
            topic for topic in self.available_topics
            if topic not in state.topics_covered
        ]
        
        # 사용 가능한 주제가 있으면 선택
        if unused_topics:
            return random.choice(unused_topics)
        
        # 모든 주제를 다뤘으면 재사용
        return random.choice(self.available_topics) if self.available_topics else "일반 정치 이슈"
    
    def initialize_topic(self) -> str:
        """초기 토론 주제 설정"""
        if self.available_topics:
            return self.available_topics[0]
        return "정치 현안"
    
    def update_state_after_message(
        self, 
        state: DebateState, 
        message: DebateMessage
    ) -> DebateState:
        """
        메시지 발송 후 상태를 업데이트합니다.
        
        Args:
            state: 현재 상태
            message: 방금 발송된 메시지
            
        Returns:
            DebateState: 업데이트된 상태
        """
        # 메시지 히스토리에 추가
        state.messages.append(message)
        
        # 주제 전환 확인
        if self.should_change_topic(state):
            new_topic = self.get_next_topic(state)
            if new_topic != state.current_topic:
                state.topics_covered.append(state.current_topic)
                state.current_topic = new_topic
        
        # 메시지에 현재 주제 반영
        message.current_topic = state.current_topic
        
        return state
    
    def should_end_debate(self, state: DebateState) -> bool:
        """
        토론을 종료해야 하는지 판단합니다.
        
        Args:
            state: 현재 상태
            
        Returns:
            bool: 종료 여부
        """
        # 50-80개 댓글 후 종료
        max_messages = random.randint(50, 80)
        if state.message_count >= max_messages:
            return True
        
        return False

