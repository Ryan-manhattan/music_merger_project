#!/bin/bash

# Music Merger Lite 실행기 (의존성 최소화)

echo "🎵 Music Merger Lite 시작 중..."
echo "📦 경량 버전 - 의존성 최소화"

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")/.."

# Python 버전 확인
echo "🐍 Python 버전:"
python3 --version

echo ""
echo "🚀 서버 시작!"
echo "📍 http://localhost:5000"
echo "🛑 Ctrl+C로 중지"
echo "💡 이 버전은 기본 기능만 제공합니다"
echo ""

# 브라우저 자동 열기 (5초 후)
(sleep 3 && open http://localhost:5000) &

# Lite 앱 실행
python3 core/app_lite.py