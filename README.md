# 🎭 ColorWar - 정치 댓글 분석 시스템

YouTube 정치 댓글을 수집하고, AI 페르소나를 생성하여 토론을 시뮬레이션하며, 뉴스 팩트체크 기능까지 제공하는 종합 정치 분석 시스템입니다.

---

## 🎯 주요 기능

### 1️⃣ **YouTube 파이프라인** (`structure/`)
- 📹 YouTube 댓글 자동 수집
- 🎤 음성 전사 (Whisper)
- 📝 내용 요약
- 🔍 좌/우 성향 자동 분류
- 🎨 주제 추출 (BERTopic + HDBSCAN)

### 2️⃣ **AI 페르소나 & 토론** (`persona/`)
- 🤖 댓글 기반 AI 페르소나 생성
- 💬 좌/우 성향별 말투 & 감정 학습
- 🎭 AI 토론 시뮬레이션
- ⚡ 실시간 대화 생성

### 3️⃣ **뉴스 팩트체크** (`factcheck/`)
- 📰 네이버 + DuckDuckGo 뉴스 검색
- 🔍 BM25 + 임베딩 하이브리드 검색
- ⭐ 신뢰도 평가 (1-10점)
- ✅ True/False/Uncertain 판정

---

## 🚀 빠른 시작

### 1. ffmpeg 설치 (필수)

YouTube 음성 전사를 위해 ffmpeg가 필요합니다:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
[ffmpeg 공식 사이트](https://ffmpeg.org/download.html)에서 다운로드

### 2. Python 의존성 설치

```bash
pip install -r require.txt
```

### 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일 생성:

```env
# 필수: YouTube API (댓글 수집)
YOUTUBE_DATA_API_KEY=your_youtube_api_key_here

# 선택: Naver API (팩트체크 품질 향상)
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
```

> 💡 자세한 설정 방법은 `require_envkey.txt` 참고

### 4. 서버 실행

```bash
python RunColorWar.py
```

### 5. 웹 접속

```
http://localhost:8000
```

---

## 📁 프로젝트 구조

```
ColorWar/
├── RunColorWar.py          # 🚀 통합 실행 파일
├── require.txt             # 📦 전체 의존성
├── require_envkey.txt      # 🔑 환경 변수 가이드
│
├── frontend/               # 💻 웹 UI
│   ├── index.html
│   └── app.js
│
├── structure/              # 📹 YouTube 파이프라인
│   ├── youtube_pipeline/   # 댓글 수집, 전사, 요약
│   ├── comments_topic/     # 주제 분석 (BERTopic)
│   └── routes/             # FastAPI 라우터
│
├── persona/                # 🤖 AI 페르소나 & 토론
│   ├── backend/            # FastAPI 서버
│   │   ├── routes/         # API 라우터
│   │   ├── services/       # 비즈니스 로직
│   │   └── main.py
│   └── model/              # 페르소나 엔진
│
└── factcheck/              # 📰 팩트체크 시스템
    ├── models/             # 검색, 판정, 신뢰도
    ├── utils/              # 텍스트 처리
    └── api.py              # FastAPI 서버
```

---

## 🌐 API 엔드포인트

### Structure (YouTube 파이프라인)
```
POST /api/structure/youtube-pipeline
POST /api/structure/analyze-topics
GET  /api/structure/status
```

### Persona (AI 페르소나 & 토론)
```
POST /api/persona/api/comments/left
POST /api/persona/api/comments/right
POST /api/persona/api/comments/generate-persona
POST /api/persona/api/debate/start
POST /api/persona/api/debate/next
GET  /api/persona/api/health
```

### Factcheck (뉴스 팩트체크)
```
POST /api/factcheck/factcheck
POST /api/factcheck/factcheck/batch
GET  /api/factcheck/health
```

### 기타
```
GET  /          # 웹 UI
GET  /docs      # API 문서 (Swagger)
GET  /health    # 전체 시스템 헬스 체크
```

---

## 🔧 핵심 기술

### AI/ML
- **LLM**: skt/kogpt2-base-v2 (CPU 최적화)
- **NLP**: BERTopic, HDBSCAN, SentenceTransformer
- **검색**: BM25 + 임베딩 하이브리드
- **STT**: Whisper (OpenAI)

### 백엔드
- **프레임워크**: FastAPI
- **검증**: Pydantic
- **웹 크롤링**: BeautifulSoup4, Requests

### 데이터 과학
- **분석**: NumPy, Scikit-learn
- **토픽 모델링**: BERTopic, UMAP, HDBSCAN

---

## 📊 사용 예시

### 1. YouTube 댓글 분석

```bash
curl -X POST http://localhost:8000/api/structure/youtube-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "topic": "현재 정부 정책",
    "rounds": 5
  }'
```

### 2. 팩트체크

```bash
curl -X POST http://localhost:8000/api/factcheck/factcheck \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "윤석열 대통령 탄핵"
  }'
```

### 3. AI 페르소나 생성

```bash
# 1. 좌파 댓글 등록
curl -X POST http://localhost:8000/api/persona/api/comments/left \
  -H "Content-Type: application/json" \
  -d '{"comment_text": "정부 정책 비판..."}'

# 2. 우파 댓글 등록
curl -X POST http://localhost:8000/api/persona/api/comments/right \
  -H "Content-Type: application/json" \
  -d '{"comment_text": "정부 정책 옹호..."}'

# 3. 페르소나 생성
curl -X POST http://localhost:8000/api/persona/api/comments/generate-persona
```

---

## ⚙️ 환경 설정

### 필수 환경 변수

| 변수명 | 설명 | 발급처 |
|--------|------|--------|
| `YOUTUBE_DATA_API_KEY` | YouTube 댓글 수집 | [Google Cloud Console](https://console.cloud.google.com/) |

### 선택적 환경 변수

| 변수명 | 설명 | 발급처 |
|--------|------|--------|
| `NAVER_CLIENT_ID` | 네이버 뉴스 검색 | [네이버 개발자센터](https://developers.naver.com/) |
| `NAVER_CLIENT_SECRET` | 네이버 API Secret | [네이버 개발자센터](https://developers.naver.com/) |
| `OPENAI_API_KEY` | OpenAI API (선택) | [OpenAI Platform](https://platform.openai.com/) |
| `OLLAMA_URL` | Ollama 로컬 LLM | [Ollama](https://ollama.ai/) |
| `OLLAMA_MODEL` | Ollama 모델명 | - |

> 💡 자세한 설정 방법: `require_envkey.txt`

---

## 🐛 문제 해결

### YouTube API 할당량 초과
```
오류: Daily Limit Exceeded
해결: Google Cloud Console에서 할당량 확인 (기본: 10,000 units/day)
```

### Naver API 없이 실행
```
상황: Naver API 키가 없음
해결: DuckDuckGo 검색이 자동으로 사용됨 (한국 뉴스 품질은 떨어질 수 있음)
```

### GPU 없이 실행
```
상황: CUDA 없음 (CPU만 사용)
해결: 자동으로 CPU 모드로 전환 (속도는 느릴 수 있음)
```

---

## 💡 주요 특징

✅ **API 키 선택적**: 네이버/YouTube API 없어도 기본 작동  
✅ **CPU 최적화**: 경량 모델 사용으로 GPU 불필요  
✅ **모듈화**: 각 기능이 독립적으로 실행 가능  
✅ **한국어 특화**: 한국 정치 댓글 및 뉴스에 최적화  
✅ **자동화**: 수집→분석→페르소나 생성→토론 전체 파이프라인  
✅ **신뢰도 기반**: 객관적인 증거 평가로 편향 최소화  

---

## 📚 문서

- **전체 구조**: `Summary.txt`
- **환경 변수**: `require_envkey.txt`
- **API 문서**: `http://localhost:8000/docs` (서버 실행 후)

---

## 🤝 기여

버그 리포트 및 기능 제안은 이슈로 등록해주세요.

---

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 제공됩니다.

---

## 📧 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---

**즐거운 사용 되세요! 🎉**
Baseline: a899970 (2025-10-30) — 기준선 확정
