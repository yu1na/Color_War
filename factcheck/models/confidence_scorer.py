"""
신뢰도 평가 시스템 (룰 기반 + LLM 자기평가)
"""
from typing import List, Dict
from datetime import datetime, timedelta
from .evidence_searcher import EvidenceSnippet
from .judge_local import JudgeResult

class ConfidenceScore:
    """신뢰도 점수"""
    def __init__(
        self,
        total_score: float,  # 0-10
        rule_score: float,   # 룰 기반 점수
        llm_score: float,    # LLM 자기평가 점수
        breakdown: Dict      # 세부 점수
    ):
        self.total_score = total_score
        self.rule_score = rule_score
        self.llm_score = llm_score
        self.breakdown = breakdown
    
    def to_dict(self) -> Dict:
        return {
            "total_score": round(self.total_score, 2),
            "rule_score": round(self.rule_score, 2),
            "llm_score": round(self.llm_score, 2),
            "breakdown": self.breakdown
        }


class ConfidenceScorer:
    """
    신뢰도 평가기
    - 룰 기반: 0-8점
    - LLM 자기평가: 0-2점
    - 최종: 1-10점
    """
    
    def __init__(
        self,
        matching_threshold: float = 0.75,  # 매칭 강도 임계값 (상향)
        recent_months: int = 12            # 최신성 기준 (개월)
    ):
        """
        Args:
            matching_threshold: 매칭 강도 임계값 (상향 조정: 0.75)
            recent_months: 최신성 판단 기준 (개월)
        """
        self.matching_threshold = matching_threshold
        self.recent_months = recent_months
    
    def score(
        self,
        evidences: List[EvidenceSnippet],
        judge_result: JudgeResult
    ) -> ConfidenceScore:
        """
        신뢰도 점수 산정
        
        Args:
            evidences: 검색된 증거 리스트
            judge_result: 판정 결과
            
        Returns:
            신뢰도 점수
        """
        # 1) 룰 기반 점수 (0-8점)
        rule_score, breakdown = self._calculate_rule_score(evidences, judge_result)
        
        # 2) LLM 자기평가 점수 (0-2점)
        llm_score = judge_result.confidence_self * 2.0
        
        # 3) 최종 점수 (1-10점)
        total = rule_score + llm_score
        
        # 4) 10점 만점으로 스케일링 (8점 → 10점)
        total_scaled = total * 1.25  # 8점 만점을 10점 만점으로 변환
        total_scaled = max(1.0, min(10.0, total_scaled))  # 1-10 범위로 클리핑
        
        return ConfidenceScore(
            total_score=total_scaled,
            rule_score=rule_score,
            llm_score=llm_score,
            breakdown=breakdown
        )
    
    def _calculate_rule_score(
        self,
        evidences: List[EvidenceSnippet],
        judge_result: JudgeResult
    ) -> tuple[float, Dict]:
        """
        룰 기반 점수 계산 (0-5점, 최종 10점 만점으로 스케일링됨)
        
        뉴스 팩트체크 시스템에 최적화:
        - 출처 수 ≥ 2: +2
        - 최신성 (12개월): +1
        - 매칭 강도: +2
        - 모순: -2
        
        Returns:
            (점수, 세부 내역)
        """
        score = 0.0
        breakdown = {}
        
        if not evidences:
            return 0.0, {"error": "Evidence 없음"}
        
        # 1) 출처 수 & 내용 일치 (+2점)
        unique_sources = len(set(ev.source for ev in evidences))
        if unique_sources >= 2:  # Pending도 포함 (판정과 무관하게 출처 평가)
            score += 2.0
            breakdown["multiple_sources"] = 2.0
        else:
            breakdown["multiple_sources"] = 0.0
        
        # 2) 최신성 (+1점)
        is_recent = self._check_recency(evidences)
        if is_recent:
            score += 1.0
            breakdown["recency"] = 1.0
        else:
            breakdown["recency"] = 0.0
        
        # 3) 매칭 강도 (Evidence 개수 고려)
        avg_score = sum(ev.final_score for ev in evidences) / len(evidences)
        max_score = max(ev.final_score for ev in evidences)
        evidence_count = len(evidences)
        
        # Evidence 개수에 따른 차등 점수
        if evidence_count == 1:
            # 1개만: 신뢰도 낮음 (우연일 수 있음)
            if avg_score >= 0.85:
                score += 1.0
                breakdown["matching_strength"] = 1.0
            else:
                score += 0.5
                breakdown["matching_strength"] = 0.5
        
        elif evidence_count == 2:
            # 2개: 중간 신뢰도
            if avg_score >= 0.75:
                score += 1.5
                breakdown["matching_strength"] = 1.5
            elif avg_score >= 0.65:
                score += 1.0
                breakdown["matching_strength"] = 1.0
            else:
                score += 0.5
                breakdown["matching_strength"] = 0.5
        
        else:  # 3개 이상
            # 3개 이상: 높은 신뢰도 (패턴 확인)
            if avg_score >= 0.72:  # 기준 완화 (0.75 → 0.72)
                score += 2.0
                breakdown["matching_strength"] = 2.0
            elif avg_score >= 0.65:
                score += 1.0
                breakdown["matching_strength"] = 1.0
            else:
                score -= 1.0
                breakdown["matching_strength"] = -1.0
        
        # 4) 상반/충돌 (-2점)
        if judge_result.contradictions:
            score -= 2.0
            breakdown["contradictions"] = -2.0
        else:
            breakdown["contradictions"] = 0.0
        
        # 5) Not-checkable이면 점수 낮춤
        if judge_result.verdict == "Not-checkable":
            score = min(score, 2.0)
            breakdown["not_checkable_penalty"] = True
        
        # 6) Uncertain이면 중간 점수
        if judge_result.verdict == "Uncertain":
            score = min(score, 3.0)
            breakdown["uncertain_penalty"] = True
        
        # 제외율 페널티 삭제 (임계값으로 품질 관리)
        
        score = max(0.0, score)  # 최저 0점 (최종 스케일링 전)
        
        return score, breakdown
    
    def _check_recency(self, evidences: List[EvidenceSnippet]) -> bool:
        """
        최신성 확인
        
        Args:
            evidences: 증거 리스트
            
        Returns:
            최신 여부 (가장 최신이 N개월 내)
        """
        try:
            dates = []
            for ev in evidences:
                try:
                    # 다양한 날짜 형식 지원
                    date_str = ev.date
                    if 'T' in date_str:  # ISO 8601 형식
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:  # 일반 형식
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    dates.append(date_obj)
                except:
                    # RFC 2822 형식 (예: Mon, 24 Mar 2025 17:10:00 +0900)
                    try:
                        from email.utils import parsedate_to_datetime
                        date_obj = parsedate_to_datetime(date_str)
                        dates.append(date_obj)
                    except:
                        continue
            
            if not dates:
                print(f"     ⚠️  최신성 판단 실패: 파싱된 날짜 0개")
                return False
            
            # timezone-aware 날짜를 naive로 변환 (비교를 위해)
            now = datetime.now()
            naive_dates = []
            for d in dates:
                if d.tzinfo is not None:
                    d_naive = d.replace(tzinfo=None)
                else:
                    d_naive = d
                
                # 미래 날짜 필터링 (뉴스 날짜가 잘못된 경우)
                if d_naive <= now:
                    naive_dates.append(d_naive)
                else:
                    print(f"     ⚠️  미래 날짜 무시: {d_naive.strftime('%Y-%m-%d')}")
            
            if not naive_dates:
                print(f"     ⚠️  최신성 판단 실패: 유효한 날짜 0개 (미래 날짜 제외)")
                return False
            
            most_recent = max(naive_dates)
            threshold_date = now - timedelta(days=30 * self.recent_months)
            
            is_recent = most_recent >= threshold_date
            print(f"     📅 최신성 체크: 최신 {most_recent.strftime('%Y-%m-%d')}, 현재 {now.strftime('%Y-%m-%d')}, 기준 {threshold_date.strftime('%Y-%m-%d')} → {'✓' if is_recent else '✗'}")
            
            return is_recent
            
        except Exception as e:
            print(f"     ⚠️  최신성 체크 예외: {e}")
            return False
    
    def get_confidence_level(self, score: float) -> str:
        """
        신뢰도 레벨 반환
        
        Args:
            score: 신뢰도 점수 (1-10)
            
        Returns:
            신뢰도 레벨 문자열
        """
        if score >= 8.5:
            return "매우 높음"
        elif score >= 7.0:
            return "높음"
        elif score >= 5.0:
            return "중간"
        elif score >= 3.0:
            return "낮음"
        else:
            return "매우 낮음"

