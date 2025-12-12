"""
FastAPI 메인 서버 (LLM 기반)
정치 유튜브 댓글 → 페르소나 생성 → AI 토론 시뮬레이터
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 설정 및 상태 관리
from config.settings import settings
from .core.state import get_app_state

# 라우터
from routes import (
    comments_router,
    persona_router,
    debate_router,
    health_router
)

# ---------------------------------------------------------
# ✅ FastAPI 초기화
# ---------------------------------------------------------
app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version
)

# ---------------------------------------------------------
# ✅ CORS 미들웨어 설정
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# ---------------------------------------------------------
# ✅ 전역 상태 초기화
# ---------------------------------------------------------
# 애플리케이션 시작 시 전역 상태 초기화
_ = get_app_state()

# ---------------------------------------------------------
# ✅ 라우터 등록
# ---------------------------------------------------------
app.include_router(comments_router)
app.include_router(persona_router)
app.include_router(debate_router)
app.include_router(health_router)

# ---------------------------------------------------------
# ✅ 루트 엔드포인트
# ---------------------------------------------------------
@app.get("/")
async def root():
    """루트 엔드포인트 - API 정보"""
    return {
        "message": f"{settings.app_title}",
        "version": settings.app_version,
        "description": settings.app_description,
        "docs": "/docs",
        "health": "/api/health"
    }


# ---------------------------------------------------------
# ✅ 로컬 실행
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("""
==========================================
🧠 정치 댓글 AI 시뮬레이터 서버 시작
------------------------------------------
📍 API 엔드포인트:
1️⃣ /api/comments/left  : 좌파 댓글 등록
2️⃣ /api/comments/right : 우파 댓글 등록
3️⃣ /api/comments/generate-persona : 페르소나 생성
4️⃣ /api/debate/start   : 토론 시작
5️⃣ /api/debate/next    : 다음 발언 생성
6️⃣ /api/health         : 헬스체크
==========================================
    """)
    uvicorn.run(
        "main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.reload
    )
