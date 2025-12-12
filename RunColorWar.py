"""
메인 서버: 프론트엔드(정적파일) 및 각 모듈(router)만 등록 (팀원 코어 분리 협업용)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 라우터/서브앱 불러오기 (각자 team의 API 구조에만 집중!)
from factcheck.api import app as factcheck_app
from persona.backend.routes import (
    comments_router,
    persona_router,
    debate_router,
    health_router as persona_health_router,
)
from structure.routes.youtube_routes import router as youtube_router
from structure.routes.topic_routes import router as topic_router
from claim_extraction.api import router as claim_extraction_router

app = FastAPI(
    title="ColorWar - 정치 댓글 분석 시스템",
    description="YouTube 댓글 분석+AI 페르소나+팩트체크 API 통합 서버",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# 각 모듈 라우터/서브앱 mount
app.mount("/api/factcheck", factcheck_app)
app.include_router(comments_router, prefix="/api/persona", tags=["Persona - 댓글"])
app.include_router(persona_router, prefix="/api/persona", tags=["Persona - 생성"])
app.include_router(debate_router, prefix="/api/persona", tags=["Persona - 토론"])
app.include_router(persona_health_router, prefix="/api/persona", tags=["Persona - 상태"])
app.include_router(youtube_router, prefix="/api/structure", tags=["Structure - YouTube"])
app.include_router(topic_router, prefix="/api/structure", tags=["Structure - 주제분석"])
app.include_router(claim_extraction_router, tags=["주장 추출"])

@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("ColorWar API (메인 화면, 프론트엔드 미탑재)")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ColorWar API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("ColorWar 통합 서버 시작 (http://localhost:8000)")
    uvicorn.run(
        "RunColorWar:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

