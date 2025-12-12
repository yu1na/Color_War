"""API 라우터"""
from .comments import router as comments_router
from .persona import router as persona_router
from .debate import router as debate_router
from .health import router as health_router

__all__ = [
    "comments_router",
    "persona_router", 
    "debate_router",
    "health_router"
]

