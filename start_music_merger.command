#!/bin/bash

# Music Merger macOS용 GUI 실행기
# 더블클릭으로 실행 가능

# 터미널 창 제목 설정
echo -ne "\033]0;Music Merger Server\007"

# 현재 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

# 환영 메시지
clear
echo "🎵====================================🎵"
echo "       Music Merger Server"
echo "🎵====================================🎵"
echo ""

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "📦 가상환경 활성화 중..."
    source venv/bin/activate
    echo "✅ 가상환경 활성화 완료"
else
    echo "⚠️  가상환경을 찾을 수 없습니다."
    echo "💡 시스템 Python을 사용합니다."
fi

echo ""
echo "🔧 Python 환경 확인..."
python3 --version
echo ""

# 브라우저 자동 열기 (5초 후)
echo "🌐 5초 후 브라우저가 자동으로 열립니다..."
(sleep 5 && open http://localhost:5000) &

# Flask 앱 실행
echo "🚀 Music Merger 서버 시작!"
echo ""
echo "📍 웹 주소: http://localhost:5000"
echo "🛑 서버 중지: Ctrl+C"
echo ""
echo "=============== 서버 로그 ==============="

# Flask 앱 실행
python3 app.py

# 종료 메시지
echo ""
echo "🎵 Music Merger 서버가 종료되었습니다."
echo ""

# 5초 후 자동 종료
echo "⏰ 5초 후 자동으로 종료됩니다..."
sleep 5