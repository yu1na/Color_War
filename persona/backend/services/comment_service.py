"""
댓글 관리 서비스
댓글 수집, 통계 조회, 초기화 등의 비즈니스 로직
"""
from typing import List, Dict
from ..core.state import AppState


class CommentService:
    """댓글 관련 비즈니스 로직"""
    
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        self.persona_engine = app_state.persona_engine
    
    def add_left_comments(self, comments: List[str]) -> Dict:
        """
        좌파 댓글 추가
        
        Args:
            comments: 댓글 리스트
            
        Returns:
            Dict: 현재 댓글 통계
        """
        if not comments:
            raise ValueError("댓글이 비어있습니다.")
        
        self.persona_engine.add_left_comments(comments)
        print(f"✓ 좌파 댓글 {len(comments)}개 추가됨 (총 {len(self.persona_engine.left_comments)}개)")
        
        return self.get_stats()
    
    def add_right_comments(self, comments: List[str]) -> Dict:
        """
        우파 댓글 추가
        
        Args:
            comments: 댓글 리스트
            
        Returns:
            Dict: 현재 댓글 통계
        """
        if not comments:
            raise ValueError("댓글이 비어있습니다.")
        
        self.persona_engine.add_right_comments(comments)
        print(f"✓ 우파 댓글 {len(comments)}개 추가됨 (총 {len(self.persona_engine.right_comments)}개)")
        
        return self.get_stats()
    
    def get_stats(self) -> Dict:
        """
        현재 수집된 댓글 통계 조회
        
        Returns:
            Dict: 댓글 통계 정보
        """
        return self.persona_engine.get_stats()
    
    def reset_comments(self) -> Dict[str, str]:
        """
        모든 댓글 및 페르소나 초기화
        
        Returns:
            Dict: 초기화 완료 메시지
        """
        self.persona_engine.reset()
        return {"message": "댓글 및 페르소나 초기화 완료"}

