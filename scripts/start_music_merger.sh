#!/bin/bash

# Music Merger Flask 앱 자동 실행 스크립트
echo "🎵 Music Merger 서버를 시작합니다..."

# 현재 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# Python 및 Flask 설치 확인
python3 --version
echo "🔧 필요한 패키지 확인 중..."

# Flask 앱 실행
echo "🚀 Music Merger 서버 시작!"
echo "📍 브라우저에서 http://localhost:5000 에 접속하세요"
echo "🛑 서버를 중지하려면 Ctrl+C를 누르세요"
echo ""

# 브라우저 자동 열기 (7초 후)
(sleep 7 && open http://localhost:5000) &

# Flask 앱 실행
python3 app.py

# 실행 완료 메시지
echo ""
echo "🎵 Music Merger 서버가 종료되었습니다."

# 터미널 창을 열어두기 위해 대기
read -p "📱 Enter 키를 눌러 종료하세요..."