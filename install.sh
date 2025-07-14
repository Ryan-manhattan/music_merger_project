#!/bin/bash

echo "🎵 Music Merger 설치 스크립트"
echo "=========================="

# Python 버전 확인
echo "1. Python 버전 확인..."
python3 --version

# 가상환경 생성
echo -e "\n2. 가상환경 생성..."
python3 -m venv venv

# 가상환경 활성화
echo -e "\n3. 가상환경 활성화..."
source venv/bin/activate

# pip 업그레이드
echo -e "\n4. pip 업그레이드..."
pip install --upgrade pip

# 의존성 설치
echo -e "\n5. 의존성 설치..."
pip install -r requirements.txt

# FFmpeg 확인
echo -e "\n6. FFmpeg 확인..."
if command -v ffmpeg &> /dev/null
then
    echo "✅ FFmpeg가 설치되어 있습니다."
    ffmpeg -version | head -n 1
else
    echo "❌ FFmpeg가 설치되어 있지 않습니다."
    echo "다음 명령어로 설치해주세요:"
    echo "  Mac: brew install ffmpeg"
    echo "  Ubuntu: sudo apt-get install ffmpeg"
    echo "  Windows: https://ffmpeg.org/download.html"
fi

echo -e "\n✅ 설치 완료!"
echo "다음 명령어로 서버를 실행하세요:"
echo "  source venv/bin/activate"
echo "  python app.py"
