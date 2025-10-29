#!/bin/bash

echo "=========================================="
echo "정치 댓글 AI 시뮬레이터 서버 시작"
echo "=========================================="
echo

# 가상환경 활성화 (존재하는 경우)
if [ -f venv/bin/activate ]; then
    echo "가상환경 활성화 중..."
    source venv/bin/activate
fi

# 백엔드 디렉토리로 이동
cd backend

# 서버 시작
echo "서버 시작 중..."
echo
python main.py

