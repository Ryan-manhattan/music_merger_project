#!/bin/bash
# Music Merger Project 자동 설치 스크립트 (Linux/macOS)

set -e  # 오류 발생 시 스크립트 중단

echo "🎵 Music Merger Project 자동 설치"
echo "=================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Python 버전 확인
check_python() {
    info "Python 버전 확인 중..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        error "Python이 설치되지 않았습니다"
        echo "Python 3.9 이상을 설치하고 다시 시도해주세요"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        error "Python 3.9 이상이 필요합니다 (현재: $PYTHON_VERSION)"
        exit 1
    fi
    
    success "Python $PYTHON_VERSION 확인됨"
}

# 시스템 의존성 설치
install_system_deps() {
    info "시스템 의존성 확인 중..."
    
    # 운영체제 확인
    OS=$(uname -s)
    
    # FFmpeg 확인
    if ! command -v ffmpeg &> /dev/null; then
        warning "FFmpeg가 설치되지 않음"
        
        case $OS in
            "Darwin")  # macOS
                if command -v brew &> /dev/null; then
                    info "Homebrew를 사용하여 FFmpeg 설치 중..."
                    brew install ffmpeg
                else
                    warning "Homebrew가 없습니다. 수동으로 FFmpeg를 설치해주세요"
                    echo "brew install ffmpeg"
                fi
                ;;
            "Linux")
                if command -v apt-get &> /dev/null; then
                    info "apt를 사용하여 FFmpeg 설치 중..."
                    sudo apt-get update
                    sudo apt-get install -y ffmpeg
                elif command -v yum &> /dev/null; then
                    info "yum을 사용하여 FFmpeg 설치 중..."
                    sudo yum install -y ffmpeg
                else
                    warning "패키지 매니저를 찾을 수 없습니다. 수동으로 FFmpeg를 설치해주세요"
                fi
                ;;
        esac
    else
        success "FFmpeg 설치됨"
    fi
    
    # Java 확인 (KoNLPy용)
    if ! command -v java &> /dev/null; then
        warning "Java가 설치되지 않음 (한국어 처리 기능 제한)"
        
        case $OS in
            "Darwin")  # macOS
                if command -v brew &> /dev/null; then
                    info "Homebrew를 사용하여 OpenJDK 설치 중..."
                    brew install openjdk@11
                else
                    warning "수동으로 Java를 설치해주세요: brew install openjdk@11"
                fi
                ;;
            "Linux")
                if command -v apt-get &> /dev/null; then
                    info "apt를 사용하여 OpenJDK 설치 중..."
                    sudo apt-get install -y openjdk-11-jdk
                elif command -v yum &> /dev/null; then
                    info "yum을 사용하여 OpenJDK 설치 중..."
                    sudo yum install -y java-11-openjdk-devel
                fi
                ;;
        esac
    else
        success "Java 설치됨"
    fi
}

# 가상 환경 생성 및 활성화
setup_venv() {
    info "가상 환경 설정 중..."
    
    if [ ! -d "venv" ]; then
        info "가상 환경 생성 중..."
        $PYTHON_CMD -m venv venv
    else
        success "가상 환경이 이미 존재함"
    fi
    
    info "가상 환경 활성화..."
    source venv/bin/activate
    
    info "pip 업그레이드..."
    pip install --upgrade pip
    
    success "가상 환경 설정 완료"
}

# Python 패키지 설치
install_packages() {
    info "Python 패키지 설치 중..."
    
    if [ -f "requirements.txt" ]; then
        info "requirements.txt에서 패키지 설치 중..."
        pip install -r requirements.txt
        success "패키지 설치 완료"
    else
        warning "requirements.txt를 찾을 수 없습니다"
        
        info "필수 패키지 개별 설치 중..."
        pip install Flask==3.0.0 beautifulsoup4==4.12.2 requests pandas numpy lxml scikit-learn
        
        info "선택적 패키지 설치 중..."
        pip install spotipy praw vaderSentiment textblob nltk || warning "일부 선택적 패키지 설치 실패"
        
        success "패키지 설치 완료"
    fi
}

# 환경변수 템플릿 생성
create_env_template() {
    info "환경변수 템플릿 생성 중..."
    
    if [ ! -f ".env" ]; then
        cat > .env.template << 'EOF'
# Music Merger Project 환경변수
# API 키들을 설정하세요

# Last.fm API
LASTFM_API_KEY=your_lastfm_api_key_here
LASTFM_API_SECRET=your_lastfm_secret_here

# Spotify API
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

# YouTube API
YOUTUBE_API_KEY=your_youtube_api_key_here

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=MusicTrendAnalyzer/1.0
EOF
        success "환경변수 템플릿 생성됨: .env.template"
        info "cp .env.template .env 실행 후 API 키를 설정하세요"
    else
        success ".env 파일이 이미 존재함"
    fi
}

# 설치 검증
verify_installation() {
    info "설치 검증 중..."
    
    # Python 스크립트로 검증
    $PYTHON_CMD -c "
import sys
modules = ['flask', 'bs4', 'requests', 'pandas', 'numpy']
failed = []

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError:
        print(f'❌ {module}')
        failed.append(module)

if failed:
    print(f'실패한 모듈: {failed}')
    sys.exit(1)
else:
    print('모든 필수 모듈 로드 성공')
"
    
    if [ $? -eq 0 ]; then
        success "설치 검증 완료"
    else
        warning "일부 모듈 로드 실패"
    fi
}

# 테스트 실행
run_test() {
    info "기본 테스트 실행 중..."
    
    if [ -f "test_new_chart_apis.py" ]; then
        timeout 30s $PYTHON_CMD test_new_chart_apis.py || warning "일부 테스트 실패 (API 키 미설정 가능)"
    else
        warning "테스트 파일을 찾을 수 없습니다"
    fi
}

# 메인 설치 프로세스
main() {
    echo "설치를 시작합니다..."
    echo
    
    # 1. Python 확인
    check_python
    
    # 2. 시스템 의존성 설치
    install_system_deps
    
    # 3. 가상 환경 설정
    setup_venv
    
    # 4. Python 패키지 설치
    install_packages
    
    # 5. 환경변수 템플릿 생성
    create_env_template
    
    # 6. 설치 검증
    verify_installation
    
    # 7. 테스트 실행
    run_test
    
    echo
    echo "🎉 설치 완료!"
    echo "=================================="
    echo "다음 단계:"
    echo "1. source venv/bin/activate  (가상 환경 활성화)"
    echo "2. cp .env.template .env     (환경변수 파일 생성)"
    echo "3. .env 파일에 API 키 설정"
    echo "4. python app.py             (앱 실행)"
    echo "5. http://localhost:5000 접속"
    echo
}

# 스크립트 실행
if [ "$0" = "${BASH_SOURCE[0]}" ]; then
    main "$@"
fi
