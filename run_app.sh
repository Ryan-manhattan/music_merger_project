#!/bin/bash

echo "================================"
echo " Music Merger App Starting..."
echo "================================"

# 현재 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 (이미 존재)
echo "Activating virtual environment..."
source venv/bin/activate

# 의존성 설치 확인
echo "Checking dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Flask 앱 실행
echo ""
echo "Starting web application..."
echo "Open browser and go to http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================"

python app.py

echo ""
echo "Application closed."
read -p "Press Enter to exit..."