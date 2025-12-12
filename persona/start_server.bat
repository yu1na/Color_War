@echo off
echo ==========================================
echo 정치 댓글 AI 시뮬레이터 서버 시작
echo ==========================================
echo.

REM 가상환경 활성화 (존재하는 경우)
if exist venv\Scripts\activate.bat (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM 백엔드 디렉토리로 이동
cd backend

REM 서버 시작
echo 서버 시작 중...
echo.
python main.py

pause

