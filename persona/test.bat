@echo off
REM 정치 댓글 전쟁 시뮬레이터 - 테스트 스크립트 (Windows)

echo ======================================
echo 정치 댓글 전쟁 시뮬레이터 테스트
echo ======================================
echo.

REM 가상환경 활성화
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo 가상환경을 찾을 수 없습니다.
    echo 먼저 install.bat을 실행하세요.
    pause
    exit /b 1
)

REM 테스트 실행
echo 서버가 http://localhost:8000 에서 실행 중이어야 합니다.
echo.
python test_api.py %*

pause

