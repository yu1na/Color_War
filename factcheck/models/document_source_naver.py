"""
네이버 뉴스 검색 (한국 뉴스 특화)
API 키 필요: https://developers.naver.com/
또는 크롤링 방식 (API 키 불필요)
"""
import requests
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime
import os
from .document_source import DocumentSource, Document


class NaverNewsSearchSource(DocumentSource):
    """
    네이버 뉴스 검색 (2가지 방법)
    1) API 방식 (API 키 필요, 안정적)
    2) 크롤링 방식 (API 키 불필요, 하지만 불안정)
    """
    
    def __init__(self, max_results: int = 10, use_api: bool = True):
        """
        Args:
            max_results: 최대 검색 결과 수
            use_api: True면 API 사용, False면 크롤링
        """
        self.max_results = max_results
        self.use_api = use_api
        
        if use_api:
            self.client_id = os.getenv("NAVER_CLIENT_ID")
            self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
            
            if self.client_id and self.client_secret:
                self.available = True
                print("  ✓ 네이버 뉴스 API 사용 가능")
            else:
                print("  ⚠ 네이버 API 키 없음 - 크롤링 모드로 전환")
                self.use_api = False
                self.available = True
        else:
            self.available = True
            print("  ✓ 네이버 뉴스 크롤링 모드")
    
    def search(self, query: str) -> List[Document]:
        """네이버 뉴스 검색"""
        if not self.available:
            return []
        
        print(f"  🔍 네이버 뉴스 검색: {query}")
        
        if self.use_api:
            return self._search_with_api(query)
        else:
            return self._search_with_crawling(query)
    
    def _search_with_api(self, query: str) -> List[Document]:
        """네이버 검색 API 사용"""
        try:
            url = "https://openapi.naver.com/v1/search/news.json"
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret
            }
            params = {
                "query": query,
                "display": self.max_results,
                "sort": "date"  # 최신순
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                documents = []
                
                for i, item in enumerate(data.get('items', [])):
                    # HTML 태그 제거
                    title = self._remove_html_tags(item.get('title', ''))
                    description = self._remove_html_tags(item.get('description', ''))
                    
                    doc = Document(
                        id=f"naver_api_{i+1}",
                        source="네이버뉴스",
                        doc_type="news",
                        title=title,
                        content=description,
                        date=item.get('pubDate', datetime.now().strftime('%Y-%m-%d')),
                        url=item.get('link', '')
                    )
                    documents.append(doc)
                
                print(f"  ✓ {len(documents)}개 네이버 뉴스 수집 완료")
                
                # 수집된 기사 제목 출력 (디버깅)
                if documents:
                    print(f"     📰 수집된 기사:")
                    for idx, doc in enumerate(documents[:3], 1):  # 최대 3개만
                        preview = doc.content[:50] + "..." if len(doc.content) > 50 else doc.content
                        print(f"        [{idx}] {doc.title}")
                        print(f"            → {preview}")
                    if len(documents) > 3:
                        print(f"        ... 외 {len(documents)-3}개")
                
                return documents
            else:
                print(f"  ⚠ API 호출 실패: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  ⚠ 네이버 API 검색 실패: {e}")
            return []
    
    def _search_with_crawling(self, query: str) -> List[Document]:
        """네이버 뉴스 크롤링 (API 키 불필요)"""
        try:
            # 키워드 추출 (러프한 검색)
            keywords = self._extract_keywords(query)
            search_query = " ".join(keywords[:3])  # 최대 3개 키워드만 사용
            
            print(f"    → 검색 키워드: '{search_query}'")
            
            # URL 인코딩
            import urllib.parse
            encoded_query = urllib.parse.quote(search_query)
            
            # 네이버 뉴스 검색 URL
            url = f"https://search.naver.com/search.naver?where=news&query={encoded_query}&sort=1"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"  ⚠ 크롤링 실패: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            documents = []
            
            # 다양한 셀렉터 시도 (네이버 HTML 구조가 자주 바뀜)
            selectors = [
                '.news_area',           # 기본
                '.news_wrap',           # 대체
                'div.group_news',       # 대체2
                'li.bx',                # 구버전
            ]
            
            news_items = []
            for selector in selectors:
                news_items = soup.select(selector)
                if news_items:
                    print(f"    → 셀렉터 '{selector}' 사용 ({len(news_items)}개 발견)")
                    break
            
            if not news_items:
                # 셀렉터 실패시 링크로 직접 검색
                print(f"    → 기본 셀렉터 실패, a 태그로 검색")
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link['href']
                    if 'news.naver.com' in href or 'news' in href:
                        title = link.get_text(strip=True)
                        if title and len(title) > 10:
                            doc = Document(
                                id=f"naver_link_{len(documents)+1}",
                                source="네이버뉴스",
                                doc_type="news",
                                title=title,
                                content=title,
                                date=datetime.now().strftime('%Y-%m-%d'),
                                url=href
                            )
                            documents.append(doc)
                            if len(documents) >= self.max_results:
                                break
            else:
                # 정상 셀렉터로 파싱
                for i, item in enumerate(news_items[:self.max_results]):
                    try:
                        # 제목 찾기 (여러 패턴 시도)
                        title = ""
                        title_elem = (item.select_one('.news_tit') or 
                                    item.select_one('a.news_tit') or
                                    item.select_one('.tit') or
                                    item.select_one('a'))
                        
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            url_link = title_elem.get('href', '')
                        else:
                            continue
                        
                        # 내용 찾기
                        content = ""
                        content_elem = (item.select_one('.dsc_txt_wrap') or
                                      item.select_one('.news_dsc') or
                                      item.select_one('.dsc'))
                        
                        if content_elem:
                            content = content_elem.get_text(strip=True)
                        
                        if not title:
                            continue
                        
                        doc = Document(
                            id=f"naver_{i+1}",
                            source="네이버뉴스",
                            doc_type="news",
                            title=title,
                            content=content if content else title,
                            date=datetime.now().strftime('%Y-%m-%d'),
                            url=url_link
                        )
                        documents.append(doc)
                        
                    except Exception as e:
                        continue
            
            if documents:
                print(f"  ✓ {len(documents)}개 네이버 뉴스 수집 완료")
                
                # 수집된 기사 제목 출력 (디버깅)
                print(f"     📰 수집된 기사:")
                for idx, doc in enumerate(documents[:3], 1):  # 최대 3개만
                    preview = doc.content[:50] + "..." if len(doc.content) > 50 else doc.content
                    print(f"        [{idx}] {doc.title}")
                    print(f"            → {preview}")
                if len(documents) > 3:
                    print(f"        ... 외 {len(documents)-3}개")
            else:
                print(f"  ⚠ 뉴스를 찾을 수 없습니다. 다른 키워드를 시도하세요.")
            
            return documents
            
        except Exception as e:
            print(f"  ⚠ 네이버 크롤링 실패: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_keywords(self, text: str) -> list:
        """텍스트에서 핵심 키워드 추출 (러프한 검색용)"""
        import re
        
        # 불용어
        stopwords = {
            '은', '는', '이', '가', '을', '를', '의', '에', '에서', '로', '으로',
            '과', '와', '도', '만', '에게', '한테', '께', '더', '라고', '이라고',
            '했다', '이다', '있다', '없다', '된다', '한다', '습니다', '합니다',
            '되었다', '되었습니다', '했습니다', '라더라', '더라', '였다'
        }
        
        # 단어 추출
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
        
        # 불용어 제거 & 길이 2 이상
        keywords = [w for w in words if w not in stopwords and len(w) >= 2]
        
        return keywords
    
    def _remove_html_tags(self, text: str) -> str:
        """HTML 태그 제거 (<b>, </b> 등)"""
        import re
        return re.sub(r'<[^>]+>', '', text)


class KoreanNewsSearchSource(DocumentSource):
    """
    한국 뉴스 통합 검색
    - 네이버 API (우선)
    - DuckDuckGo (대안)
    - 구글 뉴스 (예비)
    """
    
    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        
        # 네이버 API 시도
        self.naver = NaverNewsSearchSource(max_results=max_results, use_api=True)
        
        # DuckDuckGo 대안
        try:
            from .document_source import DuckDuckGoSearchSource
            self.ddgs = DuckDuckGoSearchSource(max_results=max_results)
            self.has_ddgs = True
        except:
            self.has_ddgs = False
        
        self.available = True
    
    def search(self, query: str) -> List[Document]:
        """한국 뉴스 통합 검색 (다중 소스)"""
        print(f"  🇰🇷 한국 뉴스 검색: {query}")
        
        documents = []
        
        # 1) 네이버 API 또는 크롤링 시도
        naver_docs = self.naver.search(query)
        if naver_docs:
            documents.extend(naver_docs)
            print(f"    ✓ 네이버: {len(naver_docs)}개")
        
        # 2) 네이버가 실패하면 DuckDuckGo로 한국 뉴스 검색
        if not documents and self.has_ddgs:
            print(f"    → 대안 검색 사용 (DuckDuckGo)")
            ddgs_docs = self.ddgs.search(query)
            documents.extend(ddgs_docs)
            if ddgs_docs:
                print(f"    ✓ DuckDuckGo: {len(ddgs_docs)}개")
        
        print(f"  ✓ 총 {len(documents)}개 뉴스 수집 완료")
        return documents

