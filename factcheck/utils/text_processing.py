"""텍스트 처리 유틸리티"""
import re
from typing import List


def split_into_sentences(text: str) -> List[str]:
    """
    문서를 문장 단위로 분할 (스니펫 생성)
    
    Args:
        text: 분할할 텍스트
        
    Returns:
        문장 리스트
    """
    # 한국어 문장 분할 (마침표, 물음표, 느낌표 기준)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def normalize_score(scores: List[float]) -> List[float]:
    """
    점수를 0-1 범위로 정규화
    
    Args:
        scores: 정규화할 점수 리스트
        
    Returns:
        정규화된 점수 리스트
    """
    if not scores:
        return []
    
    min_score = min(scores)
    max_score = max(scores)
    
    if max_score == min_score:
        return [1.0] * len(scores)
    
    return [(s - min_score) / (max_score - min_score) for s in scores]


def clean_text(text: str) -> str:
    """
    텍스트 전처리
    
    Args:
        text: 정제할 텍스트
        
    Returns:
        정제된 텍스트
    """
    # 불필요한 공백 제거
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_keywords(claim: str, max_keywords: int = 3) -> str:
    """
    주장에서 핵심 키워드만 추출 (검색 최적화)
    
    Args:
        claim: 팩트체크할 주장
        max_keywords: 최대 키워드 수
        
    Returns:
        추출된 키워드 문자열
    """
    # 1단계: 제품명 정규화 (숫자 포함 단어는 붙여쓰기)
    # "아이폰 17" → "아이폰17", "갤럭시 S26" → "갤럭시S26"
    normalized = re.sub(r'(\w+)\s+([A-Za-z]?\d+)', r'\1\2', claim)
    
    # 불용어 제거 (조사, 접속사 등)
    stopwords = [
        '이', '가', '은', '는', '을', '를', '의', '에', '에서', '로', '으로',
        '과', '와', '도', '만', '까지', '부터', '한테', '에게', '께',
        '이다', '있다', '없다', '하다', '되다', '이라', '라고', '다고',
        '그', '저', '이', '그것', '저것', '것', '수', '등', '및',
        '내년', '올해', '작년', '다음', '지난', '이번',  # 시간 표현
        '예정', '계획', '발표', '공개', '출시', '서비스', '오픈'  # 일반 동사
    ]
    
    # 공백으로 분리
    words = normalized.split()
    
    # 불용어 제거 및 2글자 이상 단어만 선택
    keywords = []
    for word in words:
        # 특수문자 제거
        cleaned_word = re.sub(r'[^\w가-힣]', '', word)
        
        # 2글자 이상이고 불용어가 아닌 경우
        if len(cleaned_word) >= 2 and cleaned_word not in stopwords:
            keywords.append(cleaned_word)
        
        if len(keywords) >= max_keywords:
            break
    
    # 키워드가 없으면 원본 반환
    if not keywords:
        return claim
    
    return ' '.join(keywords)

