# 🚀 ColorWar 빠른 시작 가이드

## ✅ 현재 구동 상태

```
✅ 서버 실행 중: http://localhost:8000
✅ YouTube 파이프라인: 작동
⏸️  팩트체크: 모듈 로딩 문제 (수정 필요)
⏸️  AI 페르소나: 모듈 로딩 문제 (수정 필요)
```

---

## 🎯 사용 가능한 기능

### 1️⃣ YouTube 댓글 수집 & 분석

**웹 UI 사용:**
```
http://localhost:8000
```

**API 직접 호출:**
```bash
curl -X POST http://localhost:8000/api/structure/youtube-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "topic": "현재 정부 정책",
    "rounds": 5
  }'
```

**기능:**
- 📹 YouTube 댓글 자동 수집
- 🎤 음성 전사 (Whisper)
- 📝 내용 요약
- 🔍 좌/우 성향 자동 분류
- 🎨 주제 추출 (BERTopic)

---

## 📊 API 문서

```
http://localhost:8000/docs
```

---

## 🔧 사용 가능한 엔드포인트

### YouTube 파이프라인
- `POST /api/structure/youtube-pipeline` - 전체 파이프라인 실행
- `POST /api/structure/analyze-topics` - 토픽 분석
- `GET /api/structure/status` - 상태 확인

### 시스템
- `GET /` - 웹 UI
- `GET /health` - 헬스 체크

---

## ⚠️ 주의사항

### ffmpeg 필수!
YouTube 음성 전사에 필요합니다:
```bash
# 설치 확인
ffmpeg -version

# macOS 설치
brew install ffmpeg
```

### YouTube API 키 필요
`.env` 파일에 추가:
```env
YOUTUBE_DATA_API_KEY=your_key_here
```

---

## 🐛 문제 해결

### "No such file or directory: 'ffmpeg'"
```bash
brew install ffmpeg
```

### "Daily Limit Exceeded" (YouTube API)
- Google Cloud Console에서 할당량 확인
- 기본: 10,000 units/day

### 팩트체크/페르소나 모듈이 안 됨
현재 모듈 로딩 문제가 있습니다. 
각 담당자가 별도로 수정 예정입니다.

---

## 📝 테스트 예시

### 1. 간단한 YouTube 영상 테스트
```bash
# 짧은 영상으로 테스트 (1-2분)
curl -X POST http://localhost:8000/api/structure/youtube-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=SHORT_VIDEO_ID"
  }'
```

### 2. 웹 UI 사용
1. http://localhost:8000 접속
2. YouTube URL 입력
3. "파이프라인 실행" 클릭
4. 결과 대기 (1-5분)

---

## 💡 팁

- **짧은 영상으로 먼저 테스트** (1-2분)
- **댓글이 많은 영상 추천** (최소 20개)
- **정치/시사 영상이 분류 정확도 높음**
- **처리 시간: 영상 길이 × 2 ~ 3배**

---

**즐거운 사용 되세요! 🎉**

