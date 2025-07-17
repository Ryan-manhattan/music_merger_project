#!/bin/bash

echo "🎵 Music Merger Server Starting..."

# 현재 스크립트의 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
source venv/bin/activate

# 서버 실행
python app.py

# 실행 후 터미널 유지
echo ""
echo "서버가 종료되었습니다."
read -p "아무 키나 눌러서 종료하세요..."