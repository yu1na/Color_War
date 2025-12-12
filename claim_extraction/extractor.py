"""
주장 추출 엔진 (Claim Extractor)
뉴스 스크립트에서 팩트체크 가능한 주장을 추출합니다.
"""

import re
from typing import List, Dict
from pathlib import Path


class ClaimExtractor:
    """룰 기반 주장 추출기"""
    
    def __init__(self):
        # 팩트체크 가능한 패턴 (댓글 특화)
        self.patterns = {
            '수치_주장': r'(\d+(?:[.,]\d+)?%?)\s*(?:를|의|으로|이|가|은|는|명|개|건|번)',
            '날짜_사건': r'(\d{1,2}월|\d{4}년|\d{1,2}일|오늘|어제|내일|지난주|이번주|작년|올해)\s*.{5,50}',
            '증감_표현': r'(증가|감소|상승|하락|급등|급락|폭증|폭락|늘어|줄어|오르|내리|망했|성공|실패).{5,50}',
            '비교_표현': r'(최다|최고|최저|역대|사상|처음|첫|유일|전부|모두|다).{5,50}',
            '인용_주장': r'(?:밝혔|주장했|발표했|말했|강조했|했다|됐다|된다).{5,50}',
            '단언_표현': r'(?:사실|진실|거짓|가짜|조작|확실|분명|절대|무조건).{5,50}',
            '정치_주장': r'(?:대통령|국회|정부|여당|야당|의원|장관|탄핵|선거|투표).{5,50}',
        }
        
        # 제외할 패턴 (질문, 추측, 의견, 욕설, 짧은 감탄사)
        self.exclude_patterns = [
            r'\?',  # 질문
            r'(?:할까|일까|까요|겠지)',  # 추측
            r'(?:보입니다|것 같습니다|듯합니다|으로 보여)',  # 추정
            r'(?:바랍니다|기대합니다|희망합니다)',  # 의견
            r'^(?:ㅋ|ㅎ|ㄷ|ㅅ){2,}',  # 자음 반복 (ㅋㅋㅋ, ㅎㅎㅎ)
            r'(?:ㅅㅂ|ㅂㅅ|ㅈㄴ|시발|병신|개새끼)',  # 욕설
        ]
    
    def extract_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분리"""
        # 문장 부호로 분리
        sentences = re.split(r'[.!?。\n]+', text)
        
        # 정제: 공백 제거, 짧은 문장 제외
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return sentences
    
    def score_claim(self, sentence: str) -> float:
        """문장의 팩트체크 가능성 점수 (0-1)"""
        score = 0.0
        
        # 패턴 매칭 점수
        for pattern_name, pattern in self.patterns.items():
            if re.search(pattern, sentence):
                score += 0.3
        
        # 숫자 포함 시 가산점
        if re.search(r'\d+', sentence):
            score += 0.2
        
        # 날짜/시간 표현 가산점
        if re.search(r'\d{1,2}월|\d{4}년|\d{1,2}일', sentence):
            score += 0.15
        
        # 구체적 인물/기관명 가산점
        if re.search(r'대통령|장관|의원|국회|청와대|정부|여당|야당', sentence):
            score += 0.1
        
        # 제외 패턴 감점
        for exclude_pattern in self.exclude_patterns:
            if re.search(exclude_pattern, sentence):
                score -= 0.5
        
        # 문장 길이 보정 (너무 짧거나 길면 감점)
        length = len(sentence)
        if length < 30 or length > 150:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def extract_claims(self, text: str, top_k: int = 5) -> List[Dict]:
        """
        텍스트에서 팩트체크 가능한 주장 추출
        
        Args:
            text: 입력 텍스트 (뉴스 스크립트)
            top_k: 추출할 주장 개수 (기본 5개)
        
        Returns:
            추출된 주장 리스트 (점수 포함)
        """
        # 문장 분리
        sentences = self.extract_sentences(text)
        
        if not sentences:
            return []
        
        # 각 문장에 점수 부여
        scored_sentences = []
        for sentence in sentences:
            score = self.score_claim(sentence)
            if score > 0.3:  # 임계값 이상만 선택
                scored_sentences.append({
                    'claim': sentence,
                    'score': round(score, 3),
                    'length': len(sentence)
                })
        
        # 점수 순으로 정렬
        scored_sentences.sort(key=lambda x: x['score'], reverse=True)
        
        # 상위 top_k개 선택
        top_claims = scored_sentences[:top_k]
        
        # 중복 제거 (유사도 체크)
        final_claims = []
        for claim in top_claims:
            is_duplicate = False
            for existing in final_claims:
                # 간단한 중복 체크 (50% 이상 겹치면 중복)
                overlap = len(set(claim['claim']) & set(existing['claim']))
                total = len(set(claim['claim']) | set(existing['claim']))
                if overlap / total > 0.5:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                final_claims.append(claim)
        
        return final_claims[:top_k]
    
    def extract_factcheck_points(self, video_id: str, base_dir: Path = None, top_k: int = 3) -> List[Dict]:
        """
        스크립트 + 댓글 통합 분석 → 팩트체크 포인트 1~3개 추출
        
        Args:
            video_id: YouTube 비디오 ID
            base_dir: 기본 디렉토리
            top_k: 추출할 팩트체크 포인트 수 (기본 3개)
        
        Returns:
            팩트체크 포인트 리스트 (가공된 문장)
        """
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[1] / "structure" / "data"
        
        script_path = base_dir / "scripts" / f"{video_id}.txt"
        comments_path = base_dir / "comments" / f"{video_id}_comments.txt"
        
        # 1단계: 스크립트에서 주장 추출
        script_claims = []
        if script_path.exists():
            with open(script_path, 'r', encoding='utf-8') as f:
                script_text = f.read()
            script_claims = self._extract_factual_claims_from_script(script_text)
            print(f"📄 스크립트에서 {len(script_claims)}개 사실 주장 추출")
        
        # 2단계: 댓글에서 논쟁 키워드 추출
        comment_keywords = []
        if comments_path.exists():
            with open(comments_path, 'r', encoding='utf-8') as f:
                comments_text = f.read()
            preprocessed = self._preprocess_comments(comments_text)
            comment_keywords = self._extract_controversy_keywords(preprocessed)
            print(f"💬 댓글에서 {len(comment_keywords)}개 논쟁 키워드 추출")
        
        # 3단계: 교집합 → 팩트체크 포인트
        factcheck_points = self._merge_to_factcheck_points(script_claims, comment_keywords)
        
        print(f"✅ 최종 {len(factcheck_points)}개 팩트체크 포인트 생성")
        
        return factcheck_points[:top_k]
    
    def _extract_factual_claims_from_script(self, text: str) -> List[str]:
        """
        스크립트에서 팩트체크 가능한 사실 주장만 추출
        
        패턴:
        - 인물명 + 직책 + 행동 (예: "장동혁 대표가 김형동 의원을 임명했다")
        - 수치/날짜 + 사건 (예: "49.42% 득표율")
        - 발언/발표 (예: "대통령이 명함에 추가하라고 했다")
        """
        claims = []
        
        # 문장 단위로 분리
        sentences = re.split(r'[.!?]\s+', text)
        
        # 팩트체크 가능한 패턴 (우선순위 순)
        patterns = [
            # 1. 인물 + 직책 + 행동 (넓게)
            r'([가-힣]+\s*(?:대통령|대표|의원|장관|후보|위원장).{10,100}(?:임명|발표|주장|밝혔|말했|결정|추진|사과|비판|지지|했습니다|했다))',
            
            # 2. SNS/명함 같은 구체적 매체
            r'([가-힣]+\s*(?:대통령|대표).{5,80}SNS.{5,40}(?:올린|발표|추가))',
            r'(명함.{5,60}(?:추가|변경|바꾸|올린))',
            
            # 3. 논란/비유 키워드
            r'([가-힣]+\s*의원.{10,60}(?:수박|내란|개엄|논란|비유|발언))',
            
            # 4. 수치/통계
            r'(\d+(?:[.,]\d+)?%?.{5,50}(?:득표|당선|증가|감소|기록))',
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15 or len(sentence) > 150:
                continue
            
            for pattern in patterns:
                match = re.search(pattern, sentence)
                if match:
                    claim = match.group(1).strip()
                    # 중복 제거
                    if claim and claim not in claims:
                        claims.append(claim)
                    break
        
        return claims[:10]  # 최대 10개
    
    def _extract_controversy_keywords(self, text: str) -> List[str]:
        """
        댓글에서 논쟁 중인 핵심 키워드 추출
        
        방법: 빈도 + 감정 표현과 함께 나타나는 단어
        """
        # 명사 추출 (간단한 방법: 2~4글자 한글 단어)
        words = re.findall(r'[가-힣]{2,4}', text)
        
        # 불용어 제거
        stopwords = {
            '이것', '그것', '저것', '여기', '거기', '저기',
            '때문', '생각', '이야기', '댓글', '영상',
            '이간질', '개처럼', '쌰우다', '망하고',  # 욕설/비방
        }
        
        # 빈도 계산
        from collections import Counter
        word_counts = Counter(w for w in words if w not in stopwords and len(w) >= 2)
        
        # 상위 10개
        top_keywords = [word for word, count in word_counts.most_common(10) if count >= 2]
        
        return top_keywords
    
    def _merge_to_factcheck_points(self, script_claims: List[str], comment_keywords: List[str]) -> List[Dict]:
        """
        스크립트 주장 + 댓글 키워드 → 팩트체크 포인트
        
        논리:
        1. 스크립트 주장 중 댓글 키워드가 포함된 것 우선
        2. 나머지 스크립트 주장 추가
        3. 가공: 불필요한 표현 제거, 핵심만 남김
        """
        factcheck_points = []
        
        # 1순위: 댓글에서 논쟁되는 주장
        for claim in script_claims:
            score = 0
            
            # 댓글 키워드와 매칭되면 점수 증가
            for keyword in comment_keywords:
                if keyword in claim:
                    score += 1
            
            if score > 0:
                # 가공: 핵심만 남김
                cleaned = self._clean_claim_for_factcheck(claim)
                if cleaned:
                    factcheck_points.append({
                        'claim': cleaned,
                        'original': claim,
                        'score': min(1.0, 0.7 + score * 0.1),  # 0.7 ~ 1.0
                        'length': len(cleaned),
                        'source': 'script+comments'
                    })
        
        # 2순위: 나머지 스크립트 주장
        for claim in script_claims:
            if not any(fp['original'] == claim for fp in factcheck_points):
                cleaned = self._clean_claim_for_factcheck(claim)
                if cleaned:
                    factcheck_points.append({
                        'claim': cleaned,
                        'original': claim,
                        'score': 0.6,
                        'length': len(cleaned),
                        'source': 'script'
                    })
        
        # 점수 순 정렬
        factcheck_points.sort(key=lambda x: x['score'], reverse=True)
        
        return factcheck_points
    
    def _clean_claim_for_factcheck(self, claim: str) -> str:
        """
        팩트체크용으로 주장 가공
        
        제거:
        - 불필요한 표현 ("~습니다", "~했다" 등)
        - 중복 공백
        
        유지:
        - 인물명, 직책, 행동, 수치
        """
        # "~습니다", "~했다" → 간결하게
        cleaned = re.sub(r'(?:습니다|했습니다|입니다|합니다)$', '', claim)
        cleaned = re.sub(r'(?:했다|한다|밝혔다|말했다)$', '', cleaned)
        
        # 중복 공백 제거
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # 너무 짧으면 제외
        if len(cleaned) < 10:
            return ''
        
        return cleaned
    
    def extract_from_file(self, video_id: str, base_dir: Path = None) -> List[Dict]:
        """
        파일에서 주장 추출
        
        Args:
            video_id: YouTube 비디오 ID
            base_dir: 기본 디렉토리 (기본값: structure/data)
        
        Returns:
            추출된 주장 리스트
        """
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[1] / "structure" / "data"
        
        # 1순위: 댓글 파일 (사용자 주장이 많음)
        comments_path = base_dir / "comments" / f"{video_id}_comments.txt"
        
        # 2순위: 스크립트 파일 (뉴스 원문)
        script_path = base_dir / "scripts" / f"{video_id}.txt"
        
        text = None
        source_type = None
        
        if comments_path.exists():
            # 댓글 파일 읽기
            with open(comments_path, 'r', encoding='utf-8') as f:
                text = f.read()
            source_type = "comments"
            print(f"📋 댓글 파일에서 주장 추출: {comments_path}")
        elif script_path.exists():
            # 스크립트 파일 읽기
            with open(script_path, 'r', encoding='utf-8') as f:
                text = f.read()
            source_type = "script"
            print(f"📋 스크립트 파일에서 주장 추출: {script_path}")
        else:
            raise FileNotFoundError(
                f"데이터 파일을 찾을 수 없습니다.\n"
                f"시도한 경로:\n"
                f"  - {comments_path}\n"
                f"  - {script_path}"
            )
        
        # 댓글 파일인 경우 전처리
        if source_type == "comments":
            text = self._preprocess_comments(text)
        
        # 주장 추출
        claims = self.extract_claims(text, top_k=5)
        
        return claims
    
    def _preprocess_comments(self, text: str) -> str:
        """
        댓글 파일 전처리
        
        Args:
            text: 원본 댓글 텍스트
        
        Returns:
            전처리된 텍스트
        """
        lines = text.split('\n')
        
        # 헤더 제거 (첫 3줄: 제목, 구분선, 빈 줄)
        if len(lines) > 3:
            lines = lines[3:]
        
        # 번호 제거 및 <br> 태그를 공백으로 변환
        processed_lines = []
        for line in lines:
            # 빈 줄 건너뛰기
            if not line.strip():
                continue
            
            # 번호 제거 (예: "1. ", "123. ")
            line = re.sub(r'^\d+\.\s*', '', line)
            
            # <br> 태그를 공백으로 변환
            line = re.sub(r'<br\s*/?>', ' ', line)
            
            # 여러 공백을 하나로
            line = re.sub(r'\s+', ' ', line).strip()
            
            if len(line) > 10:  # 너무 짧은 댓글 제외
                processed_lines.append(line)
        
        return ' '.join(processed_lines)
    
    def extract_keywords_for_factcheck(self, claim: str, max_keywords: int = 3) -> str:
        """
        댓글에서 팩트체크용 핵심 키워드만 추출
        
        Args:
            claim: 원본 댓글 (날것)
            max_keywords: 최대 키워드 수
        
        Returns:
            추출된 핵심 키워드 문자열
        """
        # 전처리: 이모지, 특수문자, 자음 반복 제거
        cleaned = re.sub(r'[😀-🙏🌀-🗿🚀-🛿🇦-🇿]+', '', claim)  # 이모지 제거
        cleaned = re.sub(r'(?:ㅋ|ㅎ|ㄷ|ㅅ){2,}', '', cleaned)  # 자음 반복 제거
        cleaned = re.sub(r'[^\w\s가-힣]', ' ', cleaned)  # 특수문자 제거
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # 공백 정리
        
        # 불용어 제거
        stopwords = [
            '이', '가', '은', '는', '을', '를', '의', '에', '에서', '로', '으로',
            '과', '와', '도', '만', '까지', '부터', '한테', '에게', '께',
            '이다', '있다', '없다', '하다', '되다', '이라', '라고', '다고',
            '그', '저', '이', '그것', '저것', '것', '수', '등', '및',
            '내년', '올해', '작년', '다음', '지난', '이번',
            '예정', '계획', '발표', '공개', '출시', '서비스', '오픈',
            '아니', '버리면', '못받는데', '무조건', '미쳤나', '같은데',
            '몰랐지', '이것들이', '마라', '몰랐어', '됐다', '어찌',
            '같은', '사람하고', '먹여살려', '되고있구나', '잘하는',
        ]
        
        # 공백으로 분리
        words = cleaned.split()
        
        # 불용어 제거 및 2글자 이상 단어만 선택
        keywords = []
        for word in words:
            # 2글자 이상이고 불용어가 아닌 경우
            if len(word) >= 2 and word not in stopwords:
                keywords.append(word)
            
            if len(keywords) >= max_keywords:
                break
        
        # 키워드가 없으면 원본에서 가장 긴 단어 3개 선택
        if not keywords:
            words_sorted = sorted(cleaned.split(), key=len, reverse=True)
            keywords = [w for w in words_sorted if len(w) >= 2][:max_keywords]
        
        result = ' '.join(keywords) if keywords else cleaned[:20]  # 최악의 경우 원본 20자
        
        return result


# 간단 테스트용
if __name__ == "__main__":
    extractor = ClaimExtractor()
    
    # 샘플 텍스트
    sample = """
    이재명 대통령은 역대 최다 득표, 과반에 가까운 득표율로 제21대 대통령에 당선됐습니다.
    최종 득표율 49.42%, 1728만 7513표를 얻으며 역대 최다 득표 기록을 세웠습니다.
    김문수 후보는 41.15% 득표율로 1439만 5639표를 얻었습니다.
    두 후보 간 표차는 289만 1000여표, 득표율로는 8.27%포인트였습니다.
    """
    
    claims = extractor.extract_claims(sample, top_k=3)
    
    print("📋 추출된 주장:")
    for i, claim in enumerate(claims, 1):
        print(f"\n[주장 {i}] (점수: {claim['score']})")
        print(f"  {claim['claim']}")

