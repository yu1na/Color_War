# 🔧 ColorWar 설치 가이드

---

## ⚠️ **중요: 필수 사전 설치**

### 1. ffmpeg 설치 (필수)

YouTube 음성 전사에 필요합니다.

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
1. [ffmpeg 공식 사이트](https://ffmpeg.org/download.html) 다운로드
2. 압축 해제 후 환경 변수 PATH에 추가

**설치 확인:**
```bash
ffmpeg -version
```

---

## 📦 **Python 패키지 설치**

### 1. 가상 환경 생성 (권장)

```bash
# conda 사용 시
conda create -n colorwar python=3.12
conda activate colorwar

# venv 사용 시
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 2. 의존성 설치

```bash
cd /Users/jinmokim/dev/ColorWar
pip install -r require.txt
```

### 3. 설치 확인

```bash
python -c "import pydantic_settings; print('✅ pydantic-settings OK')"
python -c "import fastapi; print('✅ FastAPI OK')"
python -c "import torch; print('✅ PyTorch OK')"
```

---

## 🔑 **환경 변수 설정**

### 1. .env 파일 생성

프로젝트 루트에 `.env` 파일 생성:

```bash
cd /Users/jinmokim/dev/ColorWar
touch .env
```

### 2. API 키 입력

`.env` 파일에 다음 내용 입력:

```env
# 필수: YouTube API (댓글 수집)
YOUTUBE_DATA_API_KEY=your_youtube_api_key_here

# 선택: Naver API (팩트체크 품질 향상)
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
```

> 💡 자세한 API 키 발급 방법: `require_envkey.txt` 참고

---

## 🚀 **서버 실행**

```bash
cd /Users/jinmokim/dev/ColorWar
python RunColorWar.py
```

**실행 확인:**
- 웹 UI: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/health

---

## 🐛 **문제 해결**

### 1. `No module named 'pydantic_settings'`

```bash
conda run -n colorwar pip install pydantic-settings
# 또는
pip install pydantic-settings
```

### 2. `FileNotFoundError: 'ffmpeg'`

ffmpeg가 설치되지 않았습니다. 위의 "ffmpeg 설치" 섹션 참고.

### 3. `No module named 'models.evidence_searcher'`

모듈 임포트 경로 문제입니다. `RunColorWar.py`가 최신 버전인지 확인하세요.

### 4. YouTube API 할당량 초과

```
오류: Daily Limit Exceeded
해결: Google Cloud Console에서 할당량 확인 (기본: 10,000 units/day)
```

### 5. CUDA/GPU 오류

```bash
# CPU 모드로 강제 실행
export CUDA_VISIBLE_DEVICES=""
python RunColorWar.py
```

---

## ✅ **설치 완료 체크리스트**

- [ ] ffmpeg 설치 완료
- [ ] Python 가상 환경 생성
- [ ] pip install -r require.txt 완료
- [ ] .env 파일 생성 및 API 키 입력
- [ ] python RunColorWar.py 실행 성공
- [ ] http://localhost:8000 접속 성공

---

**즐거운 사용 되세요! 🎉**

