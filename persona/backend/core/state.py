"""
전역 상태 관리
애플리케이션의 전역 상태를 관리하는 싱글톤 클래스
"""
import sys
import os
from pathlib import Path
from typing import Optional

# 상위 디렉토리를 Python 경로에 추가 (model 모듈 import를 위해)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from model.comment_persona_engine import CommentPersonaEngine
from ..models import DebateState


class AppState:
    """애플리케이션 전역 상태 관리 클래스 (싱글톤)"""
    
    _instance: Optional["AppState"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # 이미 초기화되었다면 스킵
        if self._initialized:
            return
            
        print("\n" + "="*60)
        print("🚀 애플리케이션 상태 초기화 중...")
        print("="*60)
        
        # OpenAI 설정 가져오기
        from ..config.settings import settings
        openai_api_key = settings.openai_api_key
        openai_model = settings.openai_model
        
        # 페르소나 엔진 초기화 (OpenAI 설정 전달)
        self.persona_engine = CommentPersonaEngine(
            openai_api_key=openai_api_key,
            model=openai_model
        )
        
        # 토론 관련 상태
        self.debater_manager = None  # DebaterManager는 토론 시작 시 초기화
        self.current_debate_state: Optional[DebateState] = None
        
        self._initialized = True
        print("✓ 애플리케이션 상태 초기화 완료\n")
    
    def reset_debate(self):
        """토론 상태 초기화"""
        self.debater_manager = None
        self.current_debate_state = None
        print("✓ 토론 상태 초기화 완료")
    
    def reset_all(self):
        """전체 상태 초기화"""
        self.persona_engine.reset()
        self.reset_debate()
        print("✓ 전체 상태 초기화 완료")


# 전역 상태 인스턴스 접근 함수
def get_app_state() -> AppState:
    """전역 애플리케이션 상태 인스턴스를 반환합니다."""
    return AppState()

