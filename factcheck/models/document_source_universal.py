"""
범용 뉴스 검색 (한국 + 외국 통합)
- 네이버 API: 한국 뉴스
- DuckDuckGo: 국제 뉴스
- 자동으로 둘 다 검색해서 통합
"""
from typing import List
import re
from .document_source import DocumentSource, Document, DuckDuckGoSearchSource
from .document_source_naver import NaverNewsSearchSource
from ..utils.text_processing import extract_keywords


class UniversalNewsSearchSource(DocumentSource):
    """
    범용 뉴스 검색 (한국 + 외국)
    
    전략:
    1. 네이버 API로 한국 뉴스 검색
    2. DuckDuckGo로 국제 뉴스 검색
    3. 둘 다 통합해서 반환
    
    장점:
    - 한국 이슈: 네이버 뉴스 ✅
    - 국제 이슈: DuckDuckGo ✅
    - API 키 없어도 기본 작동 ✅
    """
    
    def __init__(self, max_results_per_source: int = 10):
        """
        Args:
            max_results_per_source: 각 소스당 최대 결과 수 (기본 10개로 증가)
        """
        self.max_results = max_results_per_source
        
        # 네이버 API (한국 뉴스)
        self.naver = NaverNewsSearchSource(
            max_results=max_results_per_source,
            use_api=True  # API 키 있으면 사용, 없으면 크롤링
        )
        
        # DuckDuckGo (국제 뉴스)
        try:
            self.ddgs = DuckDuckGoSearchSource(max_results=max_results_per_source)
            self.has_ddgs = True
        except:
            self.has_ddgs = False
            print("  ⚠ DuckDuckGo 미설치")
        
        self.available = True
    
    def _extract_keywords(self, query: str) -> str:
        """
        검색 쿼리에서 핵심 키워드만 추출
        
        예:
        "윤석열 대통령이 사퇴를 발표했다" → "윤석열 대통령 사퇴 발표"
        "한강에서 괴물이 발견되었다" → "한강 괴물 발견"
        """
        # 조사 제거
        particles = [
            '이', '가', '을', '를', '에서', '의', '와', '과', '도', '만',
            '은', '는', '한테', '에게', '로', '으로', '부터', '까지'
        ]
        
        # 동사/형용사 어미 제거
        endings = [
            '했다', '한다', '되었다', '된다', '이다', '있다', '없다',
            '발표했다', '선언했다', '밝혔다', '알려졌다', '보도했다'
        ]
        
        # 우선 어미 제거
        keywords = query
        for ending in endings:
            if keywords.endswith(ending):
                keywords = keywords[:-len(ending)]
                break
        
        # 조사 제거 (단어 단위로)
        words = keywords.split()
        cleaned_words = []
        for word in words:
            # 조사로 끝나면 제거
            cleaned = word
            for particle in particles:
                if word.endswith(particle) and len(word) > len(particle):
                    cleaned = word[:-len(particle)]
                    break
            if cleaned:
                cleaned_words.append(cleaned)
        
        result = ' '.join(cleaned_words).strip()
        
        # 디버깅: 키워드 추출 결과 출력
        if result != query:
            print(f"    🔑 키워드 추출: '{query}' → '{result}'")
        
        return result if result else query  # 빈 문자열 방지
    
    def search(self, query: str) -> List[Document]:
        """
        범용 뉴스 검색 (한국 + 외국)
        
        Args:
            query: 검색 쿼리
            
        Returns:
            한국 뉴스 + 국제 뉴스 통합 결과
        """
        print(f"  🌐 범용 뉴스 검색 (한국 + 외국): {query}")
        
        # 키워드 추출 (검색 품질 향상) - 개선된 버전 사용
        search_keywords = extract_keywords(query, max_keywords=3)
        
        # 디버깅: 키워드 추출 결과 출력
        if search_keywords != query:
            print(f"    🔑 키워드 최적화: '{query}' → '{search_keywords}' (제품명 정규화 + 불용어 제거)")
        
        all_documents = []
        
        # 1) 네이버 검색 (한국 뉴스)
        print(f"    [1/2] 한국 뉴스 (네이버)...")
        naver_docs = self.naver.search(search_keywords)
        if naver_docs:
            all_documents.extend(naver_docs)
            print(f"      ✓ {len(naver_docs)}개 한국 뉴스")
        else:
            print(f"      ⚠ 한국 뉴스 0개")
        
        # 2) DuckDuckGo 검색 (국제 뉴스)
        if self.has_ddgs:
            print(f"    [2/2] 국제 뉴스 (DuckDuckGo)...")
            ddgs_docs = self.ddgs.search(search_keywords)
            if ddgs_docs:
                all_documents.extend(ddgs_docs)
                print(f"      ✓ {len(ddgs_docs)}개 국제 뉴스")
            else:
                print(f"      ⚠ 국제 뉴스 0개")
        
        # 중복 제거 (URL 기준)
        seen_urls = set()
        unique_docs = []
        for doc in all_documents:
            if doc.url not in seen_urls:
                seen_urls.add(doc.url)
                unique_docs.append(doc)
        
        print(f"  ✓ 총 {len(unique_docs)}개 뉴스 수집 (한국 + 외국)")
        
        return unique_docs[:self.max_results * 2]  # 최대 10개

