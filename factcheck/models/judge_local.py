"""
로컬 LLM 기반 판정 시스템 (API 키 불필요)
Ollama, HuggingFace 로컬 모델 등 사용 가능
"""
from typing import List, Dict
from .evidence_searcher import EvidenceSnippet


class JudgeResult:
    """판정 결과"""
    def __init__(
        self,
        verdict: str,
        reasoning: str,
        confidence_self: float,
        contradictions: List[str] = None
    ):
        self.verdict = verdict
        self.reasoning = reasoning
        self.confidence_self = confidence_self
        self.contradictions = contradictions or []
    
    def to_dict(self) -> Dict:
        return {
            "verdict": self.verdict,
            "reasoning": self.reasoning,
            "confidence_self": round(self.confidence_self, 4),
            "contradictions": self.contradictions
        }


class LocalFactCheckJudge:
    """
    로컬 LLM 기반 팩트체크 판정자 (API 키 불필요)
    
    옵션 1: Ollama (llama3, mistral 등)
    옵션 2: HuggingFace Transformers (로컬 실행)
    옵션 3: 룰 기반 간단 판정
    """
    
    def __init__(self, method: str = "rule_based"):
        """
        Args:
            method: "rule_based" | "ollama" | "huggingface"
        """
        self.method = method
        
        if method == "ollama":
            try:
                import ollama
                self.ollama = ollama
                print("✓ Ollama 로컬 LLM 사용")
            except ImportError:
                print("⚠ Ollama가 설치되지 않았습니다. 룰 기반으로 전환합니다.")
                self.method = "rule_based"
        
        elif method == "huggingface":
            try:
                from transformers import pipeline
                self.hf_pipeline = pipeline(
                    "text-generation",
                    model="meta-llama/Llama-3.2-1B-Instruct",  # 작은 모델
                    device_map="auto"
                )
                print("✓ HuggingFace 로컬 LLM 사용")
            except Exception as e:
                print(f"⚠ HuggingFace 로드 실패: {e}. 룰 기반으로 전환합니다.")
                self.method = "rule_based"
    
    def judge(self, claim: str, evidences: List[EvidenceSnippet]) -> JudgeResult:
        """판정 수행"""
        if self.method == "ollama":
            return self._judge_ollama(claim, evidences)
        elif self.method == "huggingface":
            return self._judge_huggingface(claim, evidences)
        else:
            return self._judge_rule_based(claim, evidences)
    
    def _judge_rule_based(self, claim: str, evidences: List[EvidenceSnippet]) -> JudgeResult:
        """
        개선된 룰 기반 판정 (API 키 불필요)
        관련도 기반 엄격한 판정
        """
        if not evidences:
            return JudgeResult(
                verdict="Uncertain",
                reasoning="검색된 Evidence가 없습니다.",
                confidence_self=0.0
            )
        
        # 관련도 분석
        relevance_scores = [ev.final_score for ev in evidences]
        max_relevance = max(relevance_scores)
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        high_relevance_count = sum(1 for score in relevance_scores if score >= 0.85)
        
        # Evidence 품질 체크 (최소한만)
        # 극도로 낮은 관련도만 차단
        if max_relevance < 0.5:
            return JudgeResult(
                verdict="Uncertain",
                reasoning=f"증거의 관련도가 매우 낮습니다 (최대 {max_relevance:.2f}). 더 명확한 증거가 필요합니다.",
                confidence_self=0.2
            )
        
        # 평균 관련도 체크 (완화)
        if avg_relevance < 0.45:
            return JudgeResult(
                verdict="Uncertain",
                reasoning=f"증거의 평균 관련도가 낮습니다 (평균 {avg_relevance:.2f}). 신뢰할 수 있는 증거가 부족합니다.",
                confidence_self=0.3
            )
        
        # 강한 증거 요구 제거 → 0.5 이상이면 판정 가능
        
        # 판정 로직 (완전히 중립적 - 판정하지 않음!)
        # Evidence 정보만 전달, 실제 판정은 신뢰도로!
        
        if evidences:
            reasoning = f"{len(evidences)}개의 관련 Evidence가 발견되었습니다."
            confidence = 0.5
        else:
            reasoning = "관련 Evidence를 찾을 수 없습니다."
            confidence = 0.2
        
        return JudgeResult(
            verdict="Pending",  # 임시값, main_universal.py에서 신뢰도로 판정
            reasoning=reasoning,
            confidence_self=confidence,
            contradictions=[]
        )
    
    def _judge_ollama(self, claim: str, evidences: List[EvidenceSnippet]) -> JudgeResult:
        """Ollama 로컬 LLM 사용"""
        prompt = self._build_prompt(claim, evidences)
        
        try:
            response = self.ollama.generate(
                model="llama3.2",  # 또는 "mistral"
                prompt=prompt
            )
            
            # 간단한 파싱
            text = response['response'].lower()
            
            if "true" in text or "사실" in text:
                verdict = "True"
            elif "false" in text or "거짓" in text:
                verdict = "False"
            else:
                verdict = "Uncertain"
            
            return JudgeResult(
                verdict=verdict,
                reasoning=response['response'][:200],
                confidence_self=0.7,
                contradictions=[]
            )
        except Exception as e:
            print(f"⚠ Ollama 호출 실패: {e}")
            return self._judge_rule_based(claim, evidences)
    
    def _judge_huggingface(self, claim: str, evidences: List[EvidenceSnippet]) -> JudgeResult:
        """HuggingFace 로컬 모델 사용"""
        prompt = self._build_prompt(claim, evidences)
        
        try:
            result = self.hf_pipeline(
                prompt,
                max_new_tokens=100,
                temperature=0.1
            )
            
            text = result[0]['generated_text'].lower()
            
            if "true" in text or "사실" in text:
                verdict = "True"
            elif "false" in text or "거짓" in text:
                verdict = "False"
            else:
                verdict = "Uncertain"
            
            return JudgeResult(
                verdict=verdict,
                reasoning=result[0]['generated_text'][:200],
                confidence_self=0.7,
                contradictions=[]
            )
        except Exception as e:
            print(f"⚠ HuggingFace 호출 실패: {e}")
            return self._judge_rule_based(claim, evidences)
    
    def _extract_key_entities(self, claim: str) -> List[str]:
        """
        주장에서 핵심 키워드 추출 (간단한 룰 기반)
        - 고유명사, 주요 명사 추출
        """
        # 불용어 제거
        stopwords = ["이", "그", "저", "것", "수", "등", "및", "의", "가", "을", "를", "에", "와", "과", "도"]
        
        # 주요 명사 추출 (간단한 방법: 2글자 이상 단어)
        words = claim.split()
        keywords = []
        
        for word in words:
            # 조사 제거 (간단하게)
            cleaned = word.rstrip("은는이가을를에서와과도")
            
            # 2글자 이상이고 불용어 아니면 추가
            if len(cleaned) >= 2 and cleaned not in stopwords:
                keywords.append(cleaned)
        
        # 고유명사 우선 (대문자, 영문, 숫자 포함)
        priority_keywords = [kw for kw in keywords if any(c.isupper() or c.isdigit() for c in kw)]
        
        return priority_keywords if priority_keywords else keywords[:3]  # 상위 3개
    
    def _build_prompt(self, claim: str, evidences: List[EvidenceSnippet]) -> str:
        """프롬프트 구성"""
        evidence_text = "\n".join([
            f"- {ev.source}: {ev.text}"
            for ev in evidences[:3]
        ])
        
        return f"""다음 주장이 사실인지 판단하세요.

주장: {claim}

Evidence:
{evidence_text}

판정 (True/False/Uncertain):"""

