"""
페르소나 생성 API 라우터
"""
from fastapi import APIRouter, HTTPException
from ..services.persona_service import PersonaService
from ..core.state import get_app_state

router = APIRouter(prefix="/api/comments", tags=["persona"])


@router.post("/generate-persona")
async def generate_persona():
    """
    수집된 좌/우 댓글을 기반으로 LLM이 페르소나 생성
    """
    try:
        service = PersonaService(get_app_state())
        result = service.generate_personas()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

