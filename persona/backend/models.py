"""
데이터 모델 정의
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum


class Side(str, Enum):
    """정치 성향"""
    LEFT = "left"
    RIGHT = "right"


class AnalysisRequest(BaseModel):
    """댓글 분석 요청"""
    comments_text: str = Field(..., description="분석할 댓글 텍스트")


class Argument(BaseModel):
    """논점"""
    point: str = Field(..., description="논점 내용")
    keywords: List[str] = Field(default_factory=list, description="관련 키워드")


class EmotionalPattern(BaseModel):
    """감정적 표현 패턴"""
    pattern: str = Field(..., description="패턴 설명")
    examples: List[str] = Field(default_factory=list, description="예시")


class AnalysisResult(BaseModel):
    """댓글 분석 결과"""
    left_arguments: List[Argument] = Field(default_factory=list, description="좌파 논점")
    right_arguments: List[Argument] = Field(default_factory=list, description="우파 논점")
    controversial_keywords: List[str] = Field(default_factory=list, description="논쟁적 키워드")
    left_emotional_patterns: List[EmotionalPattern] = Field(default_factory=list, description="좌파 감정 패턴")
    right_emotional_patterns: List[EmotionalPattern] = Field(default_factory=list, description="우파 감정 패턴")
    sample_comments: Dict[str, List[str]] = Field(default_factory=dict, description="샘플 댓글 (left/right)")


class DebateMessage(BaseModel):
    """토론 메시지"""
    side: Side = Field(..., description="발언자 성향")
    content: str = Field(..., description="댓글 내용")
    current_topic: str = Field(default="", description="현재 주제")
    timestamp: Optional[str] = Field(None, description="타임스탬프")


class DebateState(BaseModel):
    """토론 상태"""
    message_count: int = Field(default=0, description="총 메시지 수")
    messages: List[DebateMessage] = Field(default_factory=list, description="메시지 히스토리")
    current_topic: str = Field(default="", description="현재 토론 주제")
    topics_covered: List[str] = Field(default_factory=list, description="다뤄진 주제들")
    is_active: bool = Field(default=False, description="토론 진행 중 여부")


class DebateStartRequest(BaseModel):
    """토론 시작 요청"""
    analysis_result: AnalysisResult = Field(..., description="분석 결과")
    initial_topic: Optional[str] = Field(None, description="초기 주제")


class DebateNextRequest(BaseModel):
    """다음 댓글 생성 요청"""
    side: Side = Field(..., description="발언할 성향")


class DebateStatusResponse(BaseModel):
    """토론 상태 응답"""
    state: DebateState = Field(..., description="현재 상태")
    analysis: AnalysisResult = Field(..., description="분석 결과")


class DebateMessageResponse(BaseModel):
    """토론 메시지 응답"""
    message: DebateMessage = Field(..., description="생성된 메시지")
    state: DebateState = Field(..., description="업데이트된 상태")


class CommentSubmission(BaseModel):
    """댓글 제출 (좌파 또는 우파)"""
    comments: List[str] = Field(..., description="댓글 리스트")
    

class CommentStats(BaseModel):
    """수집된 댓글 통계"""
    left_count: int = Field(default=0, description="좌파 댓글 수")
    right_count: int = Field(default=0, description="우파 댓글 수")
    persona_ready: bool = Field(default=False, description="댓글 수집 완료 여부 (5개 이상)")
    personas_generated: bool = Field(default=False, description="페르소나 생성 완료 여부")

