"""
주장 추출 API (FastAPI Router)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from pathlib import Path

from .extractor import ClaimExtractor


router = APIRouter(prefix="/api/claim-extraction", tags=["주장 추출"])

# 전역 extractor 인스턴스
extractor = ClaimExtractor()


class ClaimExtractionRequest(BaseModel):
    """주장 추출 요청 모델"""
    video_id: str
    top_k: Optional[int] = 5


class ClaimExtractionResponse(BaseModel):
    """주장 추출 응답 모델"""
    success: bool
    video_id: str
    claims: List[Dict]
    message: Optional[str] = None


@router.post("/extract", response_model=ClaimExtractionResponse)
async def extract_claims(request: ClaimExtractionRequest):
    """
    주요 댓글 5개 추출 (날것 그대로)
    
    Args:
        video_id: YouTube 비디오 ID
        top_k: 추출할 댓글 개수 (기본 5개)
    
    Returns:
        주요 댓글 리스트 (원본 그대로)
    """
    try:
        print(f"💬 [주요 댓글 추출 요청] 비디오 ID: {request.video_id}, top_k: {request.top_k}")
        
        # 댓글에서 주요 댓글 추출 (원본 그대로)
        main_comments = extractor.extract_from_file(
            video_id=request.video_id,
            base_dir=Path(__file__).resolve().parents[1] / "structure" / "data"
        )
        
        if not main_comments:
            return ClaimExtractionResponse(
                success=False,
                video_id=request.video_id,
                claims=[],
                message="주요 댓글을 찾을 수 없습니다."
            )
        
        # top_k 적용
        main_comments = main_comments[:request.top_k or 5]
        
        print(f"✅ {len(main_comments)}개 주요 댓글 추출 완료")
        
        return ClaimExtractionResponse(
            success=True,
            video_id=request.video_id,
            claims=main_comments,
            message=f"{len(main_comments)}개의 주요 댓글을 추출했습니다."
        )
    
    except FileNotFoundError as e:
        print(f"❌ 파일 없음: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"데이터 파일을 찾을 수 없습니다: {request.video_id}"
        )
    
    except Exception as e:
        print(f"❌ 주요 댓글 추출 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"주요 댓글 추출 실패: {str(e)}"
        )


@router.post("/extract-factcheck-points", response_model=ClaimExtractionResponse)
async def extract_factcheck_points_endpoint(request: ClaimExtractionRequest):
    """
    스크립트 + 댓글 통합 분석 → 팩트체크 포인트 0~3개 추출
    
    Args:
        video_id: YouTube 비디오 ID
        top_k: 추출할 팩트체크 포인트 개수 (기본 3개)
    
    Returns:
        팩트체크 포인트 리스트 (가공된 문장)
    """
    try:
        print(f"🔍 [팩트체크 포인트 추출 요청] 비디오 ID: {request.video_id}, top_k: {request.top_k}")
        
        # 스크립트 + 댓글 통합 분석
        factcheck_points = extractor.extract_factcheck_points(
            video_id=request.video_id,
            base_dir=Path(__file__).resolve().parents[1] / "structure" / "data",
            top_k=request.top_k or 3
        )
        
        if not factcheck_points:
            return ClaimExtractionResponse(
                success=False,
                video_id=request.video_id,
                claims=[],
                message="팩트체크 포인트를 찾을 수 없습니다."
            )
        
        print(f"✅ {len(factcheck_points)}개 팩트체크 포인트 추출 완료")
        
        return ClaimExtractionResponse(
            success=True,
            video_id=request.video_id,
            claims=factcheck_points,
            message=f"{len(factcheck_points)}개의 팩트체크 포인트를 추출했습니다."
        )
    
    except FileNotFoundError as e:
        print(f"❌ 파일 없음: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"데이터 파일을 찾을 수 없습니다: {request.video_id}"
        )
    
    except Exception as e:
        print(f"❌ 팩트체크 포인트 추출 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"팩트체크 포인트 추출 실패: {str(e)}"
        )


class KeywordExtractionRequest(BaseModel):
    """키워드 추출 요청 모델"""
    claim: str


class KeywordExtractionResponse(BaseModel):
    """키워드 추출 응답 모델"""
    original_claim: str  # 원본 댓글
    keywords: str        # 추출된 키워드


@router.post("/extract-keywords", response_model=KeywordExtractionResponse)
async def extract_keywords_for_search(request: KeywordExtractionRequest):
    """
    원본 댓글에서 팩트체크용 핵심 키워드만 추출
    
    Args:
        claim: 원본 댓글 (날것)
    
    Returns:
        original_claim: 원본 댓글 그대로
        keywords: 검색용 핵심 키워드
    """
    try:
        print(f"🔑 [키워드 추출 요청] 원본: '{request.claim[:50]}...'")
        
        # 키워드 추출
        keywords = extractor.extract_keywords_for_factcheck(request.claim)
        
        print(f"✅ 키워드 추출 완료: '{keywords}'")
        
        return KeywordExtractionResponse(
            original_claim=request.claim,
            keywords=keywords
        )
    
    except Exception as e:
        print(f"❌ 키워드 추출 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"키워드 추출 실패: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok", "module": "claim_extraction"}

