#!/bin/bash
# Render 배포용 빌드 스크립트

set -e

echo "🚀 Music Merger 빌드 시작"

# pip 업그레이드
echo "📦 pip 업그레이드"
pip install --upgrade pip

# NumPy와 호환되는 패키지들을 먼저 설치
echo "🔧 핵심 의존성 설치"
pip install --no-cache-dir numpy>=1.24.0,<2.0.0
pip install --no-cache-dir scipy>=1.10.0,<1.15.0
pip install --no-cache-dir pandas>=2.0.0,<3.0.0

# 컴파일된 패키지만 사용하도록 설정
echo "🏗️  scikit-learn 설치 (바이너리만 사용)"
pip install --only-binary=all --no-cache-dir scikit-learn>=1.3.2,<1.6.0

# 나머지 requirements 설치
echo "📋 나머지 패키지 설치"
pip install --no-cache-dir -r config/requirements.txt

echo "✅ 빌드 완료!"