"""
애플리케이션 설정 관리
환경 변수 및 기본 설정을 중앙에서 관리합니다.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 서버 설정
    app_title: str = "Political Comment War Simulator (LLM 기반)"
    app_description: str = "유튜브 정치 댓글 → 페르소나 생성 → AI 토론 시뮬레이터"
    app_version: str = "3.0.0"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    
    # CORS 설정
    cors_origins: list = ["*"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    # LLM 모델 설정
    persona_model_name: str = "skt/kogpt2-base-v2"
    debater_model_name: str = "skt/kogpt2-base-v2"
    analyzer_model_name: str = "jhgan/ko-alpaca-7b"
    
    # OpenAI 설정
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    openai_model: str = "gpt-4o-mini"  # OpenAI 모델명
    
    # 디바이스 설정
    device: str = "cpu"  # "cpu" 또는 "cuda"
    use_analyzer_llm: bool = False  # 분석기에서 LLM 사용 여부 (False면 규칙 기반)
    
    # 댓글 수집 설정
    min_comments_for_persona: int = 5  # 페르소나 생성에 필요한 최소 댓글 수
    
    # 토론 설정
    initial_topic: str = "정치적 공정성"
    max_debate_messages: int = 80
    min_debate_messages: int = 50
    topic_change_interval_min: int = 8
    topic_change_interval_max: int = 12
    
    # 외부 API 키 (다른 모듈에서 사용, persona 모듈에서는 미사용)
    youtube_data_api_key: Optional[str] = None
    naver_client_id: Optional[str] = None
    naver_client_secret: Optional[str] = None
    ollama_url: Optional[str] = None
    ollama_model: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 추가 필드 무시 (Pydantic v2)


# 싱글톤 인스턴스
settings = Settings()

