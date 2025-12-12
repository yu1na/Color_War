"""
Evidence 검색 시스템 (하이브리드: BM25 + 임베딩)
- 로컬 파일 또는 웹 검색 지원
"""
import json
from typing import List, Dict, Tuple, Union
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, util
import numpy as np

from ..utils.text_processing import split_into_sentences, normalize_score, clean_text
from .document_source import DocumentSource, LocalDocumentSource, Document


class EvidenceSnippet:
    """증거 스니펫"""
    def __init__(
        self,
        text: str,
        source: str,
        doc_id: str,
        doc_type: str,
        date: str,
        title: str,
        bm25_score: float = 0.0,
        embedding_score: float = 0.0,
        final_score: float = 0.0
    ):
        self.text = text
        self.source = source
        self.doc_id = doc_id
        self.doc_type = doc_type
        self.date = date
        self.title = title
        self.bm25_score = bm25_score
        self.embedding_score = embedding_score
        self.final_score = final_score
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "source": self.source,
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "date": self.date,
            "title": self.title,
            "bm25_score": round(self.bm25_score, 4),
            "embedding_score": round(self.embedding_score, 4),
            "final_score": round(self.final_score, 4)
        }


class EvidenceSearcher:
    """
    하이브리드 Evidence 검색기
    - BM25 키워드 검색
    - 임베딩 기반 의미 유사도
    - 재정렬: 0.6 * bm25_norm + 0.4 * embed_sim
    - 로컬 파일 또는 웹 검색 지원
    """
    
    def __init__(
        self,
        document_source: DocumentSource = None,
        embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        bm25_weight: float = 0.6,
        embedding_weight: float = 0.4,
        top_n_bm25: int = 20,
        top_n_final: int = 5,
        min_relevance: float = 0.65  # 최소 관련도 임계값 (다양한 의견 수용)
    ):
        """
        Args:
            document_source: 문서 소스 (LocalDocumentSource, WebSearchDocumentSource 등)
            embedding_model_name: 임베딩 모델 이름
            bm25_weight: BM25 점수 가중치
            embedding_weight: 임베딩 점수 가중치
            top_n_bm25: BM25 상위 N개
            top_n_final: 최종 상위 N개
            min_relevance: 최소 관련도 임계값 (0.0-1.0)
        """
        self.document_source = document_source
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.bm25_weight = bm25_weight
        self.embedding_weight = embedding_weight
        self.top_n_bm25 = top_n_bm25
        self.top_n_final = top_n_final
        self.min_relevance = min_relevance if min_relevance is not None else 0.65  # 기본값 0.65 (다양한 의견 수용)
        self._last_search_metadata = {}  # 마지막 검색 메타데이터
        
        self.documents = []
        self.snippets = []
        self.bm25 = None
        self.snippet_embeddings = None
    
    def load_documents(self, documents_path: str):
        """
        로컬 파일에서 문서 로드 (하위 호환성)
        
        Args:
            documents_path: 문서 JSON 파일 경로
        """
        with open(documents_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = [
            Document(
                id=doc['id'],
                source=doc['source'],
                doc_type=doc['type'],
                title=doc['title'],
                content=doc['content'],
                date=doc['date'],
                url=doc.get('url', '')
            )
            for doc in data
        ]
        
        self._build_index(documents)
    
    def _build_index(self, documents: List[Document]):
        """
        문서 인덱스 구축 (내부 메서드)
        
        Args:
            documents: Document 객체 리스트
        """
        self.documents = documents
        
        # 문서가 없으면 에러
        if not documents:
            raise ValueError(
                "수집된 문서가 없습니다.\n"
                "해결 방법:\n"
                "  1. 웹 검색 사용: pip install duckduckgo-search\n"
                "  2. 로컬 모드 사용: python main_local.py\n"
                "  3. 하이브리드 모드: --hybrid --local-docs data/mock_documents.json"
            )
        
        # 문서 → 문장 단위 스니펫 생성 (최소 길이 필터링)
        self.snippets = []
        MIN_SNIPPET_LENGTH = 20  # 최소 20자 이상
        
        for doc in self.documents:
            sentences = split_into_sentences(doc.content)
            for sent in sentences:
                # 짧은 문장 제외
                if len(sent.strip()) < MIN_SNIPPET_LENGTH:
                    continue
                
                # 의미 없는 문장 제외
                meaningless_patterns = [
                    "...", "…", "◆", "▲", "※", "→", "·",
                    "그렇죠", "네", "아니요", "음", "어",
                    "&gt;", "&lt;", "href=", "http"
                ]
                if any(pattern in sent for pattern in meaningless_patterns):
                    continue
                
                snippet = EvidenceSnippet(
                    text=sent,
                    source=doc.source,
                    doc_id=doc.id,
                    doc_type=doc.doc_type,
                    date=doc.date,
                    title=doc.title
                )
                self.snippets.append(snippet)
        
        # 스니펫이 없으면 에러
        if not self.snippets:
            raise ValueError(
                f"문서에서 스니펫을 추출할 수 없습니다.\n"
                f"수집된 문서: {len(self.documents)}개\n"
                f"팁: 더 일반적인 키워드를 사용해보세요."
            )
        
        # BM25 인덱스 구축
        tokenized_snippets = [clean_text(s.text).split() for s in self.snippets]
        self.bm25 = BM25Okapi(tokenized_snippets)
        
        # 임베딩 생성
        snippet_texts = [s.text for s in self.snippets]
        self.snippet_embeddings = self.embedding_model.encode(
            snippet_texts,
            convert_to_tensor=True,
            show_progress_bar=True
        )
        
        print(f"✓ 문서 {len(self.documents)}개 로드")
        print(f"✓ 스니펫 {len(self.snippets)}개 생성")
        print(f"✓ BM25 인덱스 구축 완료")
        print(f"✓ 임베딩 생성 완료")
    
    def search(self, claim: str) -> List[EvidenceSnippet]:
        """
        하이브리드 검색 실행
        
        Args:
            claim: 팩트체크할 주장
            
        Returns:
            Evidence 스니펫 리스트 (상위 N개)
        """
        # 동적 문서 로드 (웹 검색 등) - 매번 새로 검색
        if self.document_source:
            print(f"  📥 문서 검색 중: {claim}")
            documents = self.document_source.search(claim)
            self._build_index(documents)
        
        if not self.snippets:
            raise ValueError("문서가 로드되지 않았습니다. load_documents()를 먼저 호출하거나 document_source를 설정하세요.")
        
        # 1) BM25 검색
        tokenized_claim = clean_text(claim).split()
        bm25_scores = self.bm25.get_scores(tokenized_claim)
        
        # BM25 상위 N개 인덱스
        top_bm25_indices = np.argsort(bm25_scores)[::-1][:self.top_n_bm25]
        
        # 2) 임베딩 유사도 계산 (BM25 상위 N개에 대해서만)
        claim_embedding = self.embedding_model.encode(claim, convert_to_tensor=True)
        
        candidates = []
        for idx in top_bm25_indices:
            snippet = self.snippets[idx]
            snippet_emb = self.snippet_embeddings[idx]
            
            # 코사인 유사도
            embedding_score = util.cos_sim(claim_embedding, snippet_emb).item()
            
            snippet.bm25_score = float(bm25_scores[idx])
            snippet.embedding_score = float(embedding_score)
            
            candidates.append((idx, snippet))
        
        # 3) 재정렬: normalized BM25 + embedding similarity
        bm25_scores_list = [s.bm25_score for _, s in candidates]
        bm25_normalized = normalize_score(bm25_scores_list)
        
        for i, (idx, snippet) in enumerate(candidates):
            final_score = (
                self.bm25_weight * bm25_normalized[i] +
                self.embedding_weight * snippet.embedding_score
            )
            snippet.final_score = final_score
        
        # 최종 점수 기준 정렬
        candidates.sort(key=lambda x: x[1].final_score, reverse=True)
        
        # 관련도 필터링: min_relevance 이상만 선택
        filtered_candidates = [
            snippet for _, snippet in candidates 
            if snippet.final_score >= self.min_relevance
        ]
        
        # 필터링 후 상위 N개 반환
        top_candidates = filtered_candidates[:self.top_n_final]
        
        # 필터링 통계 출력 (제외된 Evidence 상세)
        excluded_count = 0
        excluded = []
        
        if len(filtered_candidates) < len(candidates):
            filtered_count = len(candidates) - len(filtered_candidates)
            print(f"  ⚠️  낮은 관련도 Evidence {filtered_count}개 제외 (임계값: {self.min_relevance})")
            
            # 제외된 Evidence 목록
            excluded = [
                snippet for _, snippet in candidates 
                if snippet.final_score < self.min_relevance
            ]
            excluded_count = len(excluded)
            
            if excluded:
                print(f"\n     🗑️  제외된 Evidence ({len(excluded)}개):")
                for idx, snippet in enumerate(excluded[:5], 1):  # 최대 5개만
                    preview = snippet.text[:50] + "..." if len(snippet.text) > 50 else snippet.text
                    print(f"        [{idx}] {snippet.source} - 점수: {snippet.final_score:.2f}")
                    if snippet.title:
                        print(f"            제목: {snippet.title}")
                    print(f"            내용: {preview}")
                if len(excluded) > 5:
                    print(f"        ... 외 {len(excluded)-5}개")
                print()  # 빈 줄
        
        # 제외된 증거 메타데이터 저장 (API 응답용)
        self._last_search_metadata = {
            'total_found': len(candidates),
            'excluded_count': excluded_count,
            'returned_count': len(top_candidates)
        }
        
        return top_candidates
    
    def get_stats(self) -> Dict:
        """검색 시스템 통계"""
        return {
            "total_documents": len(self.documents),
            "total_snippets": len(self.snippets),
            "embedding_model": self.embedding_model._model_config.get('name_or_path', 'unknown'),
            "bm25_weight": self.bm25_weight,
            "embedding_weight": self.embedding_weight,
            "top_n_bm25": self.top_n_bm25,
            "top_n_final": self.top_n_final
        }

