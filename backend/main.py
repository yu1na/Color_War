"""
FastAPI 메인 서버 (LLM 기반)
정치 유튜브 댓글 → 페르소나 생성 → AI 토론 시뮬레이터
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 상위 디렉토리를 Python 경로에 추가 (model 모듈 import를 위해)
sys.path.insert(0, str(Path(__file__).parent.parent))

# 로컬 모듈 import
from model.comment_persona_engine import CommentPersonaEngine
from ai_debater import DebaterManager
from models import (
    AnalysisResult, Argument, EmotionalPattern,
    DebateState, DebateMessage, DebateStatusResponse,
    DebateMessageResponse, Side, CommentSubmission, CommentStats
)

# ---------------------------------------------------------
# ✅ FastAPI 초기화
# ---------------------------------------------------------
app = FastAPI(
    title="Political Comment War Simulator (LLM 기반)",
    description="유튜브 정치 댓글 → 페르소나 생성 → AI 토론 시뮬레이터",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# ✅ 전역 상태 관리
# ---------------------------------------------------------
persona_engine = CommentPersonaEngine()
debater_manager: Optional[DebaterManager] = None
current_state: Optional[DebateState] = None

print("\n" + "="*60)
print("🚀 서버 초기화 중...")
print("="*60)
print("LLM 로딩 완료 후 페르소나 생성이 가능합니다.\n")


# ---------------------------------------------------------
# ✅ 루트 엔드포인트
# ---------------------------------------------------------
@app.get("/")
async def root():
    # frontend 폴더는 프로젝트 루트에 있음 (backend의 형제 디렉토리)
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
    frontend_path = os.path.abspath(frontend_path)  # 절대 경로로 변환
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "Political Comment War Simulator API (LLM 기반)"}


# ---------------------------------------------------------
# ✅ 댓글 수집 API
# ---------------------------------------------------------
@app.post("/api/comments/left", response_model=CommentStats)
async def submit_left_comments(submission: CommentSubmission):
    """
    좌파 댓글 추가
    """
    if not submission.comments:
        raise HTTPException(status_code=400, detail="댓글이 비어있습니다.")
    
    persona_engine.add_left_comments(submission.comments)
    print(f"✓ 좌파 댓글 {len(submission.comments)}개 추가됨 (총 {len(persona_engine.left_comments)}개)")
    
    return CommentStats(**persona_engine.get_stats())


@app.post("/api/comments/right", response_model=CommentStats)
async def submit_right_comments(submission: CommentSubmission):
    """
    우파 댓글 추가
    """
    if not submission.comments:
        raise HTTPException(status_code=400, detail="댓글이 비어있습니다.")
    
    persona_engine.add_right_comments(submission.comments)
    print(f"✓ 우파 댓글 {len(submission.comments)}개 추가됨 (총 {len(persona_engine.right_comments)}개)")
    
    return CommentStats(**persona_engine.get_stats())


@app.get("/api/comments/stats", response_model=CommentStats)
async def get_comment_stats():
    """
    현재 수집된 댓글 수 조회
    """
    return CommentStats(**persona_engine.get_stats())


@app.post("/api/comments/reset")
async def reset_comments():
    """
    모든 댓글/페르소나 초기화
    """
    persona_engine.reset()
    return {"message": "댓글 및 페르소나 초기화 완료"}


# ---------------------------------------------------------
# ✅ 페르소나 생성 API
# ---------------------------------------------------------
@app.post("/api/comments/generate-persona")
async def generate_persona():
    """
    수집된 좌/우 댓글을 기반으로 LLM이 페르소나 생성
    """
    if len(persona_engine.left_comments) < 5 or len(persona_engine.right_comments) < 5:
        raise HTTPException(
            status_code=400,
            detail=f"댓글이 충분하지 않습니다. 좌:{len(persona_engine.left_comments)}, 우:{len(persona_engine.right_comments)} (각 5개 이상 필요)"
        )

    left_p = persona_engine.generate_persona_via_llm("left")
    right_p = persona_engine.generate_persona_via_llm("right")

    if not left_p or not right_p:
        raise HTTPException(status_code=500, detail="페르소나 생성 실패")

    return {
        "message": "페르소나 생성 완료",
        "left_persona": left_p,
        "right_persona": right_p
    }


# ---------------------------------------------------------
# ✅ 토론 시뮬레이션 API
# ---------------------------------------------------------
@app.post("/api/debate/start")
async def start_debate():
    """
    생성된 페르소나를 기반으로 토론 세션 시작
    """
    global debater_manager, current_state

    if not persona_engine.is_ready():
        raise HTTPException(status_code=400, detail="페르소나가 아직 준비되지 않았습니다. 먼저 /api/comments/generate-persona 실행")

    # 더미 분석 정보로 토론자 초기화
    dummy_analysis = AnalysisResult(
        left_arguments=[Argument(point="진보", keywords=["개혁"])],
        right_arguments=[Argument(point="보수", keywords=["안정"])],
        controversial_keywords=["정치"],
        left_emotional_patterns=[EmotionalPattern(pattern="열정적", examples=[])],
        right_emotional_patterns=[EmotionalPattern(pattern="냉정함", examples=[])],
        sample_comments={"left": [], "right": []}
    )

    debater_manager = DebaterManager(dummy_analysis, persona_engine)

    # 토론 초기 상태
    current_state = DebateState(
        message_count=0,
        messages=[],
        current_topic="정치적 공정성",
        topics_covered=[],
        is_active=True
    )

    return {
        "message": "토론 시작",
        "state": current_state,
        "persona_ready": persona_engine.is_ready()
    }


@app.post("/api/debate/next", response_model=DebateMessageResponse)
async def next_message(side: Optional[Side] = None):
    """
    다음 발언 생성 (좌/우 번갈아)
    """
    global current_state, debater_manager

    if not current_state or not current_state.is_active:
        raise HTTPException(status_code=400, detail="토론이 아직 시작되지 않았습니다.")

    if not debater_manager:
        raise HTTPException(status_code=500, detail="DebaterManager가 초기화되지 않았습니다.")

    # 발언 순서 결정
    current_state.message_count += 1
    if side is None:
        side = Side.LEFT if current_state.message_count % 2 == 1 else Side.RIGHT

    opponent_side = Side.RIGHT if side == Side.LEFT else Side.LEFT
    opponent_message = None
    for msg in reversed(current_state.messages):
        if msg.side == opponent_side:
            opponent_message = msg
            break

    print(f"{'좌파' if side == Side.LEFT else '우파'} 응답 생성 중...")
    content = debater_manager.generate_response(side, current_state, opponent_message)
    print(f"응답 완료: {content[:50]}...")

    message = DebateMessage(
        side=side,
        content=content,
        current_topic=current_state.current_topic,
        timestamp=datetime.now().isoformat()
    )
    current_state.messages.append(message)

    return DebateMessageResponse(message=message, state=current_state)


@app.get("/api/debate/status", response_model=DebateStatusResponse)
async def debate_status():
    """
    현재 토론 상태 조회
    """
    global current_state
    if not current_state:
        raise HTTPException(status_code=404, detail="진행 중인 토론이 없습니다.")
    return DebateStatusResponse(state=current_state)


@app.post("/api/debate/reset")
async def reset_debate():
    """
    토론 세션 초기화
    """
    global current_state
    current_state = None
    return {"message": "토론이 초기화되었습니다."}


# ---------------------------------------------------------
# ✅ 헬스체크
# ---------------------------------------------------------
@app.get("/api/health")
async def health_check():
    import torch
    return {
        "status": "healthy",
        "cuda_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "persona_stats": persona_engine.get_stats()
    }


# ---------------------------------------------------------
# ✅ 정적 프론트엔드 제공
# ---------------------------------------------------------
try:
    # frontend 폴더는 프로젝트 루트에 있음 (backend의 형제 디렉토리)
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    frontend_dir = os.path.abspath(frontend_dir)  # 절대 경로로 변환
    if os.path.exists(frontend_dir):
        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
        print(f"✓ 프론트엔드 마운트 완료: {frontend_dir}")
except Exception as e:
    print(f"⚠ 프론트엔드 마운트 실패: {e}")


# ---------------------------------------------------------
# ✅ 로컬 실행
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("""
==========================================
🧠 정치 댓글 AI 시뮬레이터 서버 시작
------------------------------------------
1️⃣ /api/comments/left  : 좌파 댓글 등록
2️⃣ /api/comments/right : 우파 댓글 등록
3️⃣ /api/comments/generate-persona : 페르소나 생성
4️⃣ /api/debate/start   : 토론 시작
5️⃣ /api/debate/next    : 다음 발언 생성
==========================================
    """)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
