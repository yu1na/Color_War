"""
YouTube 파이프라인 라우터
댓글 수집 → 분석 → 요약 → 분류
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from pathlib import Path
import sys

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_pipeline.youtube_full_pipeline import YouTubeFullPipeline

router = APIRouter()

# 전역 파이프라인 인스턴스
pipeline = YouTubeFullPipeline(base_dir=Path(__file__).parent.parent)


class YouTubeRequest(BaseModel):
    youtube_url: str


class YouTubeResponse(BaseModel):
    success: bool
    video_id: str
    summary: Dict
    analysis: Dict
    debate: List[Dict]
    message: str


@router.post("/youtube-pipeline", response_model=YouTubeResponse)
async def run_youtube_pipeline(request: YouTubeRequest):
    """
    YouTube 전체 파이프라인 실행
    1. 오디오 다운로드
    2. 음성 전사
    3. 요약 생성
    4. 댓글 수집
    5. 댓글 분석 (좌/우 분류)
    """
    try:
        print(f"\n{'='*60}")
        print(f"YouTube 파이프라인 시작: {request.youtube_url}")
        print(f"{'='*60}\n")
        
        result = pipeline.run_full_pipeline(youtube_url=request.youtube_url)
        
        if not result:
            raise HTTPException(
                status_code=400,
                detail="파이프라인 처리 실패: 빈 결과"
            )
        
        return YouTubeResponse(
            success=True,
            video_id=result.get('video_id', ''),
            summary=result.get('summary', {}),
            analysis=result.get('analysis', {}),
            debate=result.get('debate', []),
            message="YouTube 파이프라인 완료"
        )
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"파이프라인 처리 실패: {str(e)}"
        )


@router.get("/status")
async def get_status():
    """파이프라인 상태 조회"""
    return {
        "status": "ready",
        "pipeline": "YouTube Full Pipeline",
        "base_dir": str(pipeline.base_dir)
    }

