"""
문서 소스 인터페이스
로컬 파일 또는 웹 검색을 선택할 수 있는 확장 가능한 구조
"""
from abc import ABC, abstractmethod
from typing import List, Dict
import json
import requests
from datetime import datetime


class Document:
    """문서 클래스"""
    def __init__(self, id: str, source: str, doc_type: str, title: str, content: str, date: str, url: str = ""):
        self.id = id
        self.source = source
        self.doc_type = doc_type
        self.title = title
        self.content = content
        self.date = date
        self.url = url
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source,
            "type": self.doc_type,
            "title": self.title,
            "content": self.content,
            "date": self.date,
            "url": self.url
        }


class DocumentSource(ABC):
    """문서 소스 인터페이스"""
    
    @abstractmethod
    def search(self, query: str) -> List[Document]:
        """쿼리에 맞는 문서 검색"""
        pass


class LocalDocumentSource(DocumentSource):
    """
    로컬 JSON 파일에서 문서 로드 (개발/테스트용)
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.documents = []
        self._load_documents()
    
    def _load_documents(self):
        """JSON 파일 로드"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.documents = [
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
    
    def search(self, query: str) -> List[Document]:
        """모든 문서 반환 (쿼리 무시)"""
        return self.documents


class WebSearchDocumentSource(DocumentSource):
    """
    웹 검색을 통한 실시간 문서 수집
    - Google 뉴스
    - 네이버 뉴스
    - 기사 크롤링
    """
    
    def __init__(self, search_engine: str = "google", max_results: int = 10):
        """
        Args:
            search_engine: "google", "naver", "both"
            max_results: 최대 검색 결과 수
        """
        self.search_engine = search_engine
        self.max_results = max_results
    
    def search(self, query: str) -> List[Document]:
        """실시간 웹 검색"""
        documents = []
        
        if self.search_engine in ["google", "both"]:
            documents.extend(self._search_google(query))
        
        if self.search_engine in ["naver", "both"]:
            documents.extend(self._search_naver(query))
        
        return documents[:self.max_results]
    
    def _search_google(self, query: str) -> List[Document]:
        """Google 뉴스 검색 (Custom Search API 사용)"""
        # TODO: Google Custom Search API 키 필요
        # https://developers.google.com/custom-search/v1/overview
        
        # 임시 구현 (실제로는 API 호출)
        print(f"  🔍 Google 뉴스 검색: {query}")
        
        # 실제 구현 예시:
        # api_key = os.getenv("GOOGLE_API_KEY")
        # cx = os.getenv("GOOGLE_CX")  # Custom Search Engine ID
        # url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={query}"
        # response = requests.get(url)
        # data = response.json()
        
        # 임시로 빈 리스트 반환
        return []
    
    def _search_naver(self, query: str) -> List[Document]:
        """네이버 뉴스 검색 (Naver Search API 사용)"""
        # TODO: 네이버 API 키 필요
        # https://developers.naver.com/docs/serviceapi/search/news/news.md
        
        print(f"  🔍 네이버 뉴스 검색: {query}")
        
        # 실제 구현 예시:
        # client_id = os.getenv("NAVER_CLIENT_ID")
        # client_secret = os.getenv("NAVER_CLIENT_SECRET")
        # url = f"https://openapi.naver.com/v1/search/news.json?query={query}"
        # headers = {
        #     "X-Naver-Client-Id": client_id,
        #     "X-Naver-Client-Secret": client_secret
        # }
        # response = requests.get(url, headers=headers)
        # data = response.json()
        
        # 임시로 빈 리스트 반환
        return []


class DuckDuckGoSearchSource(DocumentSource):
    """
    DuckDuckGo 검색 (API 키 불필요, 무료)
    개발 단계에서 즉시 사용 가능
    """
    
    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        try:
            # 새로운 패키지명 시도
            try:
                from ddgs import DDGS
            except ImportError:
                # 이전 패키지명 폴백
                from duckduckgo_search import DDGS
            
            self.ddgs = DDGS()
            self.available = True
            print("  ✓ DuckDuckGo 검색 엔진 사용 가능")
        except ImportError:
            self.available = False
            print("  ⚠ DuckDuckGo 미설치 - pip install ddgs")
    
    def search(self, query: str) -> List[Document]:
        """DuckDuckGo 뉴스 검색 (API 키 불필요)"""
        if not self.available:
            print("  ⚠ DuckDuckGo 검색 불가능 - 패키지 설치 필요")
            return []
        
        print(f"  🔍 DuckDuckGo 검색: {query}")
        
        try:
            documents = []
            
            # 1) 뉴스 검색 시도
            try:
                # ddgs 9.x 버전 사용법: 위치 인자로 query 전달
                results = list(self.ddgs.news(query, max_results=self.max_results))
                
                for i, result in enumerate(results):
                    doc = Document(
                        id=f"news_{i+1}",
                        source=result.get('source', 'Web'),
                        doc_type="news",
                        title=result.get('title', ''),
                        content=result.get('body', result.get('title', '')),
                        date=result.get('date', datetime.now().strftime('%Y-%m-%d')),
                        url=result.get('url', '')
                    )
                    documents.append(doc)
            except Exception as e:
                print(f"    ⚠ 뉴스 검색 실패: {e}")
            
            # 2) 뉴스가 없으면 일반 텍스트 검색
            if not documents:
                print(f"    → 일반 검색으로 전환")
                try:
                    # ddgs 9.x 버전 사용법: 위치 인자로 query 전달
                    results = list(self.ddgs.text(query, max_results=self.max_results))
                    
                    for i, result in enumerate(results):
                        doc = Document(
                            id=f"text_{i+1}",
                            source="Web Search",
                            doc_type="web",
                            title=result.get('title', ''),
                            content=result.get('body', result.get('title', '')),
                            date=datetime.now().strftime('%Y-%m-%d'),
                            url=result.get('href', '')
                        )
                        documents.append(doc)
                except Exception as e:
                    print(f"    ⚠ 일반 검색도 실패: {e}")
            
            print(f"  ✓ {len(documents)}개 웹 문서 수집 완료")
            
            # 수집된 기사 제목 출력 (디버깅)
            if documents:
                print(f"     📰 수집된 기사:")
                for idx, doc in enumerate(documents[:3], 1):  # 최대 3개만
                    preview = doc.content[:50] + "..." if len(doc.content) > 50 else doc.content
                    print(f"        [{idx}] {doc.title}")
                    print(f"            → {preview}")
                if len(documents) > 3:
                    print(f"        ... 외 {len(documents)-3}개")
            elif not documents:
                print(f"  💡 팁: 더 일반적인 키워드를 사용하거나 --hybrid 모드를 사용하세요")
            
            return documents
            
        except Exception as e:
            print(f"  ⚠ 웹 검색 실패: {e}")
            return []


class HybridDocumentSource(DocumentSource):
    """
    하이브리드 소스: 로컬 + 웹 검색
    - 로컬 데이터 우선 사용
    - 부족하면 웹 검색 추가
    """
    
    def __init__(self, local_path: str = None, web_source: DocumentSource = None):
        self.local_source = LocalDocumentSource(local_path) if local_path else None
        self.web_source = web_source or DuckDuckGoSearchSource(max_results=5)
    
    def search(self, query: str) -> List[Document]:
        """로컬 + 웹 검색 결합"""
        documents = []
        
        # 1. 로컬 문서
        if self.local_source:
            documents.extend(self.local_source.search(query))
            print(f"  ✓ 로컬 문서: {len(documents)}개")
        
        # 2. 웹 검색 추가
        web_docs = self.web_source.search(query)
        documents.extend(web_docs)
        print(f"  ✓ 총 문서: {len(documents)}개 (로컬 + 웹)")
        
        return documents

