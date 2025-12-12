"""
댓글 주제 분석 라우터
BERTopic + HDBSCAN을 사용한 토픽 모델링
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from pathlib import Path
import sys

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "comments_topic" / "src"))

router = APIRouter()


class TopicAnalysisRequest(BaseModel):
    comments_file: str  # 댓글 파일 경로 (txt)
    target_topics: int = 8


class TopicAnalysisResponse(BaseModel):
    success: bool
    topics: Dict
    message: str


@router.post("/analyze-topics", response_model=TopicAnalysisResponse)
async def analyze_topics(request: TopicAnalysisRequest):
    """
    댓글 주제 분석
    BERTopic + HDBSCAN으로 토픽 모델링 수행
    """
    try:
        from comments_topic import (
            parse_comments,
            prepare_comments,
            build_topic_model,
            generate_topic_report
        )
        
        print(f"\n{'='*60}")
        print(f"토픽 분석 시작: {request.comments_file}")
        print(f"{'='*60}\n")
        
        # 파일 존재 확인
        comments_path = Path(request.comments_file)
        if not comments_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"댓글 파일을 찾을 수 없습니다: {request.comments_file}"
            )
        
        # 댓글 로드
        with open(comments_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        comments = parse_comments(lines)
        if not comments:
            raise HTTPException(
                status_code=400,
                detail="유효한 댓글이 없습니다"
            )
        
        print(f"✓ {len(comments)}개 댓글 로드")
        
        # 전처리
        filtered, _ = prepare_comments(comments)
        print(f"✓ {len(filtered)}개 댓글 필터링")
        
        # 토픽 모델링
        topic_model, labels = build_topic_model(filtered, request.target_topics)
        print(f"✓ {len(set(labels))}개 토픽 발견")
        
        # 리포트 생성
        report_path = comments_path.parent / "comments_result" / f"{comments_path.stem}_topics.txt"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        result = generate_topic_report(
            model=topic_model,
            labels=labels,
            comments=filtered,
            output_file=str(report_path)
        )
        
        print(f"✓ 리포트 저장: {report_path}")
        print(f"{'='*60}\n")
        
        return TopicAnalysisResponse(
            success=True,
            topics=result,
            message=f"토픽 분석 완료: {len(set(labels))}개 주제 발견"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"토픽 분석 실패: {str(e)}"
        )


@router.get("/topic-status")
async def get_topic_status():
    """토픽 분석 상태 조회"""
    return {
        "status": "ready",
        "model": "BERTopic + HDBSCAN",
        "language": "Korean"
    }

