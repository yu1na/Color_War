"""
댓글 수집 API 라우터
"""
from fastapi import APIRouter, HTTPException
from ..models import CommentSubmission, CommentStats
from ..services.comment_service import CommentService
from ..core.state import get_app_state

router = APIRouter(prefix="/api/comments", tags=["comments"])


@router.post("/left", response_model=CommentStats)
async def submit_left_comments(submission: CommentSubmission):
    """좌파 댓글 추가"""
    try:
        service = CommentService(get_app_state())
        stats = service.add_left_comments(submission.comments)
        return CommentStats(**stats)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/right", response_model=CommentStats)
async def submit_right_comments(submission: CommentSubmission):
    """우파 댓글 추가"""
    try:
        service = CommentService(get_app_state())
        stats = service.add_right_comments(submission.comments)
        return CommentStats(**stats)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats", response_model=CommentStats)
async def get_comment_stats():
    """현재 수집된 댓글 수 조회"""
    service = CommentService(get_app_state())
    stats = service.get_stats()
    return CommentStats(**stats)


@router.post("/reset")
async def reset_comments():
    """모든 댓글/페르소나 초기화"""
    service = CommentService(get_app_state())
    return service.reset_comments()

