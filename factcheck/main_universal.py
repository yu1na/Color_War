"""
범용 팩트체크 (한국 + 외국 뉴스 통합)

사용법:
    # 한국 + 외국 뉴스 모두 검색
    python main_universal.py --claim "비트코인 가격이 급등했다"
    python main_universal.py --claim "삼성전자 반도체 수출이 증가했다"
    
    # 배치 처리
    python main_universal.py --batch claims.json
"""
import argparse
import json
import os
from typing import List, Dict
from dotenv import load_dotenv
from .models.evidence_searcher import EvidenceSearcher, EvidenceSnippet
from .models.judge_local import LocalFactCheckJudge
from .models.confidence_scorer import ConfidenceScorer
from .models.document_source_universal import UniversalNewsSearchSource


class FactCheckResult:
    """팩트체크 결과"""
    def __init__(
        self,
        claim: str,
        verdict: str,
        reasoning: str,
        confidence_score: float,
        confidence_level: str,
        evidences: List[EvidenceSnippet],
        score_breakdown: Dict
    ):
        self.claim = claim
        self.verdict = verdict
        self.reasoning = reasoning
        self.confidence_score = confidence_score
        self.confidence_level = confidence_level
        self.evidences = evidences
        self.score_breakdown = score_breakdown
    
    def to_dict(self) -> Dict:
        return {
            "claim": self.claim,
            "verdict": self.verdict,
            "reasoning": self.reasoning,
            "confidence_score": round(self.confidence_score, 2),
            "confidence_level": self.confidence_level,
            "evidences": [
                {
                    "text": ev.text,
                    "source": ev.source,
                    "date": ev.date,
                    "relevance": round(ev.final_score, 2)
                }
                for ev in self.evidences
            ],
            "score_breakdown": self.score_breakdown
        }
    
    def print_summary(self):
        """결과 요약 출력"""
        verdict_emoji = {
            "True": "✅",
            "False": "❌",
            "Uncertain": "❓",
            "Not-checkable": "🚫"
        }
        
        print("\n" + "="*80)
        print(f"📋 주장: {self.claim}")
        print("="*80)
        print(f"{verdict_emoji.get(self.verdict, '?')} 판정: {self.verdict}")
        print(f"⭐ 신뢰도: {self.confidence_score:.1f}/10 ({self.confidence_level})")
        print(f"\n💡 판정 근거:")
        print(f"   {self.reasoning}")
        
        if self.evidences:
            print(f"\n📚 참고 Evidence ({len(self.evidences)}개):\n")
            for idx, ev in enumerate(self.evidences, 1):
                print(f"   [{idx}] {ev.source} ({ev.date})")
                print(f"       {ev.text}")
                print(f"       관련도: {ev.final_score:.2f}\n")
        
        if self.score_breakdown:
            print("📊 신뢰도 세부:")
            for key, value in self.score_breakdown.items():
                if isinstance(value, (int, float)):
                    print(f"   - {key}: {value}")
                else:
                    print(f"   - {key}: {value}")
        
        print("="*80)


def normalize_claim(claim: str) -> str:
    """주장 정규화"""
    return claim.strip()


def check_claim(claim: str, searcher, judge, scorer) -> FactCheckResult:
    """단일 주장 팩트체크"""
    
    # 입력 정규화만 수행 (검증 제거 - 자동화 시스템용)
    claim = normalize_claim(claim)
    
    print(f"\n🔍 팩트체크 대상: {claim}")
    
    # Evidence 검색
    print("   [1/3] 뉴스 검색 중 (한국 + 외국)...")
    try:
        evidences = searcher.search(claim)
        print(f"   ✓ {len(evidences)}개 Evidence 수집 완료")
    except Exception as e:
        print(f"   ⚠ Evidence 검색 실패: {e}")
        return None
    
    # 판정
    print("   [2/3] 판정 중...")
    judge_result = judge.judge(claim, evidences)
    print(f"   ✓ 판정 완료: {judge_result.verdict}")
    
    # 신뢰도 산정
    print("   [3/3] 신뢰도 평가 중...")
    confidence = scorer.score(evidences, judge_result)
    confidence_level = scorer.get_confidence_level(confidence.total_score)
    print(f"   ✓ 신뢰도: {confidence.total_score:.1f}/10 ({confidence_level})")
    
    # 신뢰도 기반 최종 판정 (객관적!)
    final_verdict = judge_result.verdict
    final_reasoning = judge_result.reasoning
    
    # 신뢰도로 판정 (10점 만점 기준)
    if confidence.total_score < 5.5:
        final_verdict = "False"
        final_reasoning = f"{judge_result.reasoning} (신뢰도 {confidence.total_score:.1f}/10 - 낮음)"
    elif 5.5 <= confidence.total_score <= 7.0:
        final_verdict = "Uncertain"
        final_reasoning = f"{judge_result.reasoning} (신뢰도 {confidence.total_score:.1f}/10 - 애매함)"
    else:  # > 7.0
        final_verdict = "True"
        final_reasoning = f"{judge_result.reasoning} (신뢰도 {confidence.total_score:.1f}/10 - 높음)"
    
    # 결과 생성
    result = FactCheckResult(
        claim=claim,
        verdict=final_verdict,
        reasoning=final_reasoning,
        confidence_score=confidence.total_score,
        confidence_level=confidence_level,
        evidences=evidences,
        score_breakdown=confidence.breakdown
    )
    
    return result


def main():
    # .env 파일 로드
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="범용 팩트체크 (한국 + 외국 뉴스)")
    parser.add_argument("--claim", type=str, help="팩트체크할 주장")
    parser.add_argument("--batch", type=str, help="주장 리스트 JSON 파일")
    parser.add_argument("--output", type=str, default="results_universal.json", help="결과 저장 경로")
    parser.add_argument("--max-results", type=int, default=10, help="소스당 최대 결과 수 (기본 10개)")
    
    args = parser.parse_args()
    
    # 시스템 초기화
    print("="*80)
    print("🌐 범용 팩트체크 시스템 (한국 + 외국 뉴스 통합)")
    print("="*80)
    
    try:
        # 1) 범용 뉴스 소스
        print("\n[1/3] 범용 뉴스 소스 초기화 중...")
        universal_source = UniversalNewsSearchSource(max_results_per_source=args.max_results)
        
        # 2) Evidence 검색기
        searcher = EvidenceSearcher(
            document_source=universal_source,
            embedding_model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        print("✓ Evidence 검색 시스템 준비 완료")
        
        # 3) 판정자
        print("\n[2/3] 판정 시스템 초기화 중...")
        judge = LocalFactCheckJudge(method="rule_based")
        print("✓ 판정 시스템 준비 완료")
        
        # 4) 신뢰도 평가기
        print("\n[3/3] 신뢰도 평가 시스템 초기화 중...")
        scorer = ConfidenceScorer()
        print("✓ 신뢰도 평가 준비 완료")
        
        print("\n" + "="*80)
        print("✅ 시스템 초기화 완료!")
        print("💡 팁: 네이버 API 키 설정하면 한국 뉴스 검색 향상!")
        print("   export NAVER_CLIENT_ID='your-id'")
        print("   export NAVER_CLIENT_SECRET='your-secret'")
        print("="*80)
        
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 단일 체크
    if args.claim:
        result = check_claim(args.claim, searcher, judge, scorer)
        if result:
            result.print_summary()
    
    # 배치 처리
    elif args.batch:
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                if data and isinstance(data[0], dict):
                    claims = [item.get('claim') or item.get('keyword') or item.get('text') for item in data]
                else:
                    claims = data
            else:
                print("⚠ 잘못된 JSON 형식")
                return
            
            results = []
            for i, claim in enumerate(claims, 1):
                print(f"\n[{i}/{len(claims)}] 처리 중...")
                result = check_claim(claim, searcher, judge, scorer)
                if result:
                    results.append(result)
                    result.print_summary()
            
            # 결과 저장
            output_data = [r.to_dict() for r in results]
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"\n💾 결과 저장: {args.output}")
            
        except Exception as e:
            print(f"❌ 배치 처리 실패: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("\n⚠ --claim 또는 --batch 옵션 필요")
        print("\n사용 예시:")
        print("  python main_universal.py --claim \"비트코인 가격이 급등했다\"")
        print("  python main_universal.py --batch claims.json")


if __name__ == "__main__":
    main()

