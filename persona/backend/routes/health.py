"""
헬스체크 API 라우터
"""
import torch
from fastapi import APIRouter
from ..core.state import get_app_state

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """서버 상태 및 시스템 정보 조회"""
    app_state = get_app_state()
    
    return {
        "status": "healthy",
        "cuda_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "persona_stats": app_state.persona_engine.get_stats()
    }

