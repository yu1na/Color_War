#!/usr/bin/env python3
"""
배치 테스트: 여러 루머 케이스 일괄 검증
"""
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# 절대 경로로 모듈 임포트
sys.path.insert(0, str(Path(__file__).parent.parent))

from factcheck.models.document_source_universal import UniversalNewsSearchSource
from factcheck.models.evidence_searcher import EvidenceSearcher
from factcheck.models.judge_local import LocalFactCheckJudge
from factcheck.models.confidence_scorer import ConfidenceScorer

def main():
    load_dotenv()
    
    # 테스트 케이스 로드
    test_file = Path(__file__).parent / "rumor_test_cases.json"
    with open(test_file, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print("=" * 80)
    print("🧪 루머 배치 테스트 (8개 케이스)")
    print("=" * 80)
    print()
    
    # 시스템 초기화
    doc_source = UniversalNewsSearchSource()
    evidence_searcher = EvidenceSearcher(
        document_source=doc_source,
        top_n_bm25=20,
        top_n_final=5,
        min_relevance=0.65  # 다양한 의견 수용
    )
    judge = LocalFactCheckJudge()
    scorer = ConfidenceScorer()
    
    print("✓ 시스템 초기화 완료\n")
    
    # 결과 저장
    results = []
    
    for i, case in enumerate(test_cases, 1):
        claim = case["claim"]
        category = case["category"]
        
        print(f"\n[{i}/8] 🔍 {claim}")
        print(f"   카테고리: {category}")
        print("-" * 80)
        
        try:
            # 1) Evidence 검색
            evidences = evidence_searcher.search(claim)
            
            if not evidences:
                print("   ⚠️  증거 없음 → Uncertain")
                results.append({
                    "claim": claim,
                    "category": category,
                    "verdict": "Uncertain",
                    "confidence": 0.0,
                    "reasoning": "증거 없음",
                    "evidence_count": 0
                })
                continue
            
            # 2) 판정
            judge_result = judge.judge(claim, evidences)
            
            # 3) 신뢰도
            confidence_result = scorer.score(
                evidences=evidences,
                judge_result=judge_result
            )
            
            # 4) 신뢰도 기반 최종 판정 (객관적!)
            final_verdict = judge_result.verdict
            final_reasoning = judge_result.reasoning
            
            # 신뢰도로 판정
            if confidence_result.total_score < 4.5:
                final_verdict = "False"
                final_reasoning = f"{judge_result.reasoning} (신뢰도 {confidence_result.total_score:.1f}/10 - 낮음)"
            elif 4.5 <= confidence_result.total_score <= 5.5:
                final_verdict = "Uncertain"
                final_reasoning = f"{judge_result.reasoning} (신뢰도 {confidence_result.total_score:.1f}/10 - 애매함)"
            else:  # > 5.5
                final_verdict = "True"
                final_reasoning = f"{judge_result.reasoning} (신뢰도 {confidence_result.total_score:.1f}/10 - 높음)"
            
            # 결과 저장
            result = {
                "claim": claim,
                "category": category,
                "verdict": final_verdict,
                "confidence": confidence_result.total_score,
                "reasoning": final_reasoning,
                "evidence_count": len(evidences)
            }
            results.append(result)
            
            # 결과 출력
            verdict_emoji = {
                "True": "✅",
                "False": "❌",
                "Uncertain": "❓"
            }.get(final_verdict, "❔")
            
            print(f"   {verdict_emoji} 판정: {final_verdict}")
            print(f"   ⭐ 신뢰도: {confidence_result.total_score:.1f}/10")
            print(f"   💡 근거: {final_reasoning}")
            print(f"   📚 증거: {len(evidences)}개")
            
            # 상세 증거 내용 출력
            if evidences:
                print(f"\n   📄 수집된 증거 상세:")
                for idx, ev in enumerate(evidences, 1):
                    print(f"\n      [{idx}] {ev.source} ({ev.date or '날짜 미상'})")
                    if ev.title:
                        print(f"          제목: {ev.title}")
                    print(f"          내용: {ev.text[:150]}{'...' if len(ev.text) > 150 else ''}")
                    print(f"          관련도: {ev.final_score:.2f}")
            print()
            
        except Exception as e:
            print(f"   ❌ 오류: {str(e)}")
            results.append({
                "claim": claim,
                "category": category,
                "verdict": "Error",
                "confidence": 0.0,
                "reasoning": str(e),
                "evidence_count": 0
            })
    
    # 최종 요약
    print("\n" + "=" * 80)
    print("📊 배치 테스트 요약")
    print("=" * 80)
    
    verdict_counts = {}
    for r in results:
        verdict = r["verdict"]
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
    
    print(f"\n총 {len(results)}개 케이스:")
    for verdict, count in sorted(verdict_counts.items()):
        emoji = {"True": "✅", "False": "❌", "Uncertain": "❓", "Error": "⚠️"}.get(verdict, "❔")
        print(f"  {emoji} {verdict}: {count}개")
    
    print("\n" + "=" * 80)
    
    # 결과 저장
    output_file = Path(__file__).parent / "batch_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 결과 저장: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()

