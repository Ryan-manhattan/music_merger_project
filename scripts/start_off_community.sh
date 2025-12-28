#!/bin/bash

# OFF THE COMMUNITY Flask 앱 자동 실행 스크립트
echo ""
echo "========================================"
echo "  OFF THE COMMUNITY 서버 시작"
echo "========================================"
echo ""

# 현재 스크립트가 있는 디렉토리의 상위(루트) 디렉토리로 이동
cd "$(dirname "$0")/.."

# 현재 디렉토리 확인
echo "[INFO] 작업 디렉토리: $(pwd)"
echo ""

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "[WARNING] .env 파일이 없습니다."
    echo "[WARNING] .env.example을 참고하여 .env 파일을 생성해주세요."
    echo ""
    if [ -f ".env.example" ]; then
        echo "[INFO] .env.example 파일을 복사하여 .env를 만드시겠습니까? (y/n)"
        read -r create_env
        if [ "$create_env" = "y" ] || [ "$create_env" = "Y" ]; then
            cp ".env.example" ".env"
            echo "[OK] .env 파일이 생성되었습니다. 필요한 값들을 채워주세요."
            echo ""
        fi
    fi
fi

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3가 설치되어 있지 않거나 PATH에 없습니다."
    echo "[ERROR] Python3를 설치해주세요."
    exit 1
fi

python3 --version
echo ""

# 가상환경 확인 및 활성화
if [ -d "venv" ]; then
    echo "[INFO] 가상환경 활성화 중..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "[INFO] 가상환경 활성화 중..."
    source .venv/bin/activate
else
    echo "[WARNING] 가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다."
fi

echo ""

# 필요한 패키지 확인 (선택적)
echo "[INFO] 필요한 패키지 확인 중..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "[WARNING] Flask가 설치되어 있지 않습니다."
    echo "[INFO] requirements.txt에서 패키지를 설치하시겠습니까? (y/n)"
    read -r install_packages
    if [ "$install_packages" = "y" ] || [ "$install_packages" = "Y" ]; then
        echo "[INFO] 패키지 설치 중..."
        pip3 install -r requirements.txt
        echo ""
    fi
fi

echo ""
echo "========================================"
echo "  서버 시작"
echo "========================================"
echo ""
echo "[INFO] 브라우저에서 http://localhost:5000 에 접속하세요"
echo "[INFO] 서버를 중지하려면 Ctrl+C를 누르세요"
echo ""

# 브라우저 자동 열기 (7초 후)
(sleep 7 && open http://localhost:5000) &

# Flask 앱 실행
python3 app.py

# 실행 완료 메시지
echo ""
echo "========================================"
echo "  서버가 종료되었습니다"
echo "========================================"
echo ""
echo "[INFO] 문제가 발생했다면:"
echo "  - .env 파일의 SUPABASE_URL, SUPABASE_KEY가 올바른지 확인하세요"
echo "  - 터미널에서 'python3 app.py'를 직접 실행해보세요"
echo ""

# 터미널 창을 열어두기 위해 대기
read -p "Enter 키를 눌러 종료하세요..."


