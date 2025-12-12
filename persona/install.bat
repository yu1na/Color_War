@echo off
echo ==========================================
echo 정치 댓글 전쟁 시뮬레이터 설치
echo ==========================================
echo.

REM Python 버전 확인
python --version
if %errorlevel% neq 0 (
    echo Python이 설치되지 않았습니다.
    echo Python 3.9 이상을 설치해주세요.
    pause
    exit /b 1
)

echo.
echo 가상환경 생성 중...
python -m venv venv

echo.
echo 가상환경 활성화 중...
call venv\Scripts\activate.bat

echo.
echo 의존성 설치 중...
cd backend
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ==========================================
echo 설치 완료!
echo ==========================================
echo.
echo 서버 실행: start_server.bat
echo API 테스트: python test_api.py
echo.
pause

