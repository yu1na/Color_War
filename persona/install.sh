#!/bin/bash

echo "=========================================="
echo "정치 댓글 전쟁 시뮬레이터 설치"
echo "=========================================="
echo

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "Python3가 설치되지 않았습니다."
    echo "Python 3.9 이상을 설치해주세요."
    exit 1
fi

python3 --version

echo
echo "가상환경 생성 중..."
python3 -m venv venv

echo
echo "가상환경 활성화 중..."
source venv/bin/activate

echo
echo "의존성 설치 중..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "=========================================="
echo "설치 완료!"
echo "=========================================="
echo
echo "서버 실행: ./start_server.sh"
echo "API 테스트: python test_api.py"
echo

# 실행 권한 부여
chmod +x ../start_server.sh
chmod +x install.sh

