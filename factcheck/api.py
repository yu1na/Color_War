"""
FastAPI 팩트체크 API 서버

사용법:
    # 서버 시작
    uvicorn api:app --reload --host 0.0.0.0 --port 8000
    
    # 테스트
    curl -X POST http://localhost:8000/factcheck \
         -H "Content-Type: application/json" \
         -d '{"claim": "M5맥북 출시 임박"}'
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from .models.evidence_searcher import EvidenceSearcher
from .models.judge_local import LocalFactCheckJudge
from .models.confidence_scorer import ConfidenceScorer
from .models.document_source_universal import UniversalNewsSearchSource

# 환경변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI(
    title="팩트체크 API",
    description="뉴스 기반 팩트체크 시스템 (한국 + 해외)",
    version="1.0.0"
)

# CORS 설정 (다른 팀원 프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에선 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수로 시스템 초기화 (재사용)
searcher = None
judge = None
scorer = None


def initialize_system():
    """팩트체크 시스템 초기화 (지연 초기화)"""
    global searcher, judge, scorer
    
    if searcher and judge and scorer:
        return  # 이미 초기화됨
    
    print("🚀 팩트체크 시스템 초기화 중...")
    
    try:
        # 1) 범용 뉴스 소스
        universal_source = UniversalNewsSearchSource(max_results_per_source=10)
        
        # 2) Evidence 검색기
        searcher = EvidenceSearcher(
            document_source=universal_source,
            embedding_model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # 3) 판정자
        judge = LocalFactCheckJudge(method="rule_based")
        
        # 4) 신뢰도 평가기
        scorer = ConfidenceScorer()
        
        print("✅ 팩트체크 시스템 초기화 완료!")
        
        # 네이버 API 키 확인
        if os.getenv("NAVER_CLIENT_ID"):
            print("✅ 네이버 API 키 설정됨")
        else:
            print("⚠️  네이버 API 키 미설정 (크롤링 모드)")
    
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        raise


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 시스템 초기화 시도 (실패해도 계속 진행)"""
    try:
        initialize_system()
    except Exception as e:
        print(f"⚠️  시작 시 초기화 실패, 첫 요청 시 재시도: {e}")


# Request/Response 모델
class FactCheckRequest(BaseModel):
    claim: str
    max_results: Optional[int] = 10
    
    class Config:
        json_schema_extra = {
            "example": {
                "claim": "M5맥북 출시 임박",
                "max_results": 10
            }
        }


class EvidenceResponse(BaseModel):
    text: str
    source: str
    date: str
    relevance: float


class SearchMetadata(BaseModel):
    """검색 메타데이터"""
    total_found: int = 0
    excluded_count: int = 0
    returned_count: int = 0


class FactCheckResponse(BaseModel):
    claim: str
    verdict: str
    confidence_score: float
    confidence_level: str
    reasoning: str
    evidences: List[EvidenceResponse]
    score_breakdown: dict
    search_metadata: Optional[SearchMetadata] = None


class BatchFactCheckRequest(BaseModel):
    claims: List[str]
    max_results: Optional[int] = 10


class HealthResponse(BaseModel):
    status: str
    system: str
    naver_api: bool


# API 엔드포인트
@app.get("/", response_model=dict)
async def root():
    """API 루트"""
    return {
        "message": "팩트체크 API 서버",
        "version": "1.0.0",
        "endpoints": {
            "POST /factcheck": "단일 주장 팩트체크",
            "POST /factcheck/batch": "배치 팩트체크",
            "GET /health": "헬스체크"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy" if searcher else "initializing",
        "system": "ready",
        "naver_api": bool(os.getenv("NAVER_CLIENT_ID"))
    }


@app.post("/factcheck", response_model=FactCheckResponse)
async def factcheck(request: FactCheckRequest):
    """
    단일 주장 팩트체크
    
    Args:
        request: 팩트체크 요청 (claim, max_results)
    
    Returns:
        팩트체크 결과 (verdict, confidence, evidences 등)
    """
    # 지연 초기화 (첫 요청 시 초기화)
    if not searcher or not judge or not scorer:
        try:
            initialize_system()
        except Exception as e:
            raise HTTPException(
                status_code=503, 
                detail=f"시스템 초기화 실패: {str(e)}"
            )
    
    try:
        claim = request.claim.strip()
        
        print(f"🔍 [팩트체크 요청] 받은 주장: '{claim}'")
        
        if not claim:
            raise HTTPException(status_code=400, detail="주장이 비어있습니다")
        
        # 1) Evidence 검색
        print(f"📥 [검색 시작] 주장: '{claim}'")
        
        try:
            evidences = searcher.search(claim)
        except ValueError as e:
            # 검색 결과가 없거나 스니펫 생성 실패
            error_msg = str(e)
            print(f"⚠️  검색 실패: {error_msg}")
            
            # 수집된 문서 수 확인
            doc_count = 0
            if "수집된 문서:" in error_msg:
                try:
                    doc_count = int(error_msg.split("수집된 문서:")[1].split("개")[0].strip())
                except:
                    pass
            
            # 판정 로직
            if doc_count == 0:
                # 문서 0개 = 검색 자체가 안됨 = 판단 불가
                verdict = "Uncertain"
                reasoning = "관련 뉴스나 자료를 찾을 수 없습니다. 검색어를 바꿔보세요."
                confidence = 1.0
            elif doc_count <= 2:
                # 문서 1~2개 = 관련 뉴스가 거의 없음 = 거짓일 가능성
                verdict = "False"
                reasoning = f"관련 뉴스가 매우 적습니다 ({doc_count}개). 해당 주장은 사실이 아니거나 확인되지 않은 정보일 가능성이 높습니다."
                confidence = 3.0
            else:
                # 문서는 있지만 스니펫 생성 실패 = 내용이 너무 짧거나 품질 낮음 = 거짓
                verdict = "False"
                reasoning = f"수집된 자료({doc_count}개)의 품질이 낮거나 관련성이 부족합니다. 해당 주장은 확인되지 않은 정보일 가능성이 높습니다."
                confidence = 3.5
            
            return FactCheckResponse(
                claim=claim,
                verdict=verdict,
                confidence_score=confidence,
                confidence_level="낮음" if confidence < 5 else "매우 낮음",
                reasoning=reasoning,
                evidences=[],
                score_breakdown={"문서_수": doc_count, "스니펫_생성": "실패"},
                search_metadata=SearchMetadata(total_found=doc_count, excluded_count=0, returned_count=0)
            )
        
        if not evidences:
            # 문서는 수집되었지만 관련도가 낮아 모두 제외된 경우
            # = 검색은 되지만 관련 내용이 없음 = 거짓일 가능성
            metadata = searcher._last_search_metadata if hasattr(searcher, '_last_search_metadata') else {}
            total_found = metadata.get('total_found', 0)
            
            return FactCheckResponse(
                claim=claim,
                verdict="False",
                confidence_score=2.5,
                confidence_level="매우 낮음",
                reasoning=f"수집된 자료({total_found}개) 중 관련성 있는 증거를 찾을 수 없습니다. 해당 주장은 확인되지 않은 정보일 가능성이 높습니다.",
                evidences=[],
                score_breakdown={"문서_수": total_found, "관련_증거": 0},
                search_metadata=SearchMetadata(total_found=total_found, excluded_count=total_found, returned_count=0)
            )
        
        # 2) 판정
        judge_result = judge.judge(claim, evidences)
        
        # 3) 신뢰도 평가
        confidence = scorer.score(evidences, judge_result)
        confidence_level = scorer.get_confidence_level(confidence.total_score)
        
        # 4) 최종 판정 (신뢰도 기반)
        if confidence.total_score < 5.5:
            final_verdict = "False"
            final_reasoning = f"{judge_result.reasoning} (신뢰도 {confidence.total_score:.1f}/10 - 낮음)"
        elif 5.5 <= confidence.total_score <= 7.0:
            final_verdict = "Uncertain"
            final_reasoning = f"{judge_result.reasoning} (신뢰도 {confidence.total_score:.1f}/10 - 애매함)"
        else:
            final_verdict = "True"
            final_reasoning = f"{judge_result.reasoning} (신뢰도 {confidence.total_score:.1f}/10 - 높음)"
        
        # 5) 응답 생성
        return FactCheckResponse(
            claim=claim,
            verdict=final_verdict,
            confidence_score=round(confidence.total_score, 2),
            confidence_level=confidence_level,
            reasoning=final_reasoning,
            evidences=[
                EvidenceResponse(
                    text=ev.text,
                    source=ev.source,
                    date=ev.date,
                    relevance=round(ev.final_score, 2)
                )
                for ev in evidences
            ],
            score_breakdown=confidence.breakdown,
            search_metadata=SearchMetadata(**searcher._last_search_metadata) if hasattr(searcher, '_last_search_metadata') else None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"팩트체크 실패: {str(e)}")


@app.post("/factcheck/batch")
async def batch_factcheck(request: BatchFactCheckRequest):
    """
    배치 팩트체크 (여러 주장 한번에)
    
    Args:
        request: 배치 요청 (claims 리스트)
    
    Returns:
        팩트체크 결과 리스트
    """
    # 지연 초기화 (첫 요청 시 초기화)
    if not searcher or not judge or not scorer:
        try:
            initialize_system()
        except Exception as e:
            raise HTTPException(
                status_code=503, 
                detail=f"시스템 초기화 실패: {str(e)}"
            )
    
    try:
        results = []
        
        for claim in request.claims:
            try:
                # 단일 팩트체크 재사용
                result = await factcheck(FactCheckRequest(
                    claim=claim,
                    max_results=request.max_results
                ))
                results.append(result)
            except Exception as e:
                # 개별 실패는 에러 포함해서 계속 진행
                results.append({
                    "claim": claim,
                    "error": str(e)
                })
        
        return {"results": results, "total": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"배치 팩트체크 실패: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

