"""
채팅 시뮬레이션 API 라우터
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Body
from ..models import DebateStatusResponse, DebateMessageResponse, Side
from ..services.debate_service import DebateService
from ..core.state import get_app_state

router = APIRouter(prefix="/api/debate", tags=["debate"])


@router.post("/start")
async def start_debate(
    initial_topic: Optional[str] = Body(None),
    keywords: Optional[List[str]] = Body(None),
    summary_sentences: Optional[List[str]] = Body(None)
):
    """
    생성된 페르소나를 기반으로 채팅 세션 시작
    
    Args:
        initial_topic: 초기 토론 주제 (선택)
        keywords: 토론 키워드 리스트 (하위 호환성)
        summary_sentences: 영상 요약 문장 리스트 (youtube_full_pipeline에서 전달)
    """
    try:
        service = DebateService(get_app_state())
        result = service.start_debate(
            initial_topic=initial_topic, 
            keywords=keywords,
            summary_sentences=summary_sentences
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/next", response_model=DebateMessageResponse)
async def next_message(side: Optional[Side] = None):
    """다음 채팅 생성 (좌/우 번갈아)"""
    try:
        service = DebateService(get_app_state())
        result = service.generate_next_message(side)
        return DebateMessageResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=DebateStatusResponse)
async def debate_status():
    """현재 채팅 상태 조회"""
    try:
        service = DebateService(get_app_state())
        result = service.get_debate_status()
        return DebateStatusResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reset")
async def reset_debate():
    """채팅 세션 초기화"""
    service = DebateService(get_app_state())
    return service.reset_debate()

