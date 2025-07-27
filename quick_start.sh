#!/bin/bash

# 빠른 실행용 스크립트 (백그라운드 실행)

cd "$(dirname "$0")"

echo "🎵 Music Merger 백그라운드 시작..."

# 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 백그라운드에서 Flask 앱 실행
python3 app.py &
APP_PID=$!

echo "✅ 서버 시작됨 (PID: $APP_PID)"
echo "📍 http://localhost:5000"

# 브라우저 열기
sleep 2
open http://localhost:5000

echo "🛑 서버 중지: kill $APP_PID"