@echo off
:: Music Merger Project Windows 자동 설치 스크립트

echo 🎵 Music Merger Project 자동 설치 (Windows)
echo ==================================================

:: 색상 및 유니코드 지원
chcp 65001 > nul

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️ 관리자 권한으로 실행하는 것이 권장됩니다
    echo 일부 시스템 의존성 설치가 제한될 수 있습니다
    pause
)

:: Python 버전 확인
echo.
echo 🔍 Python 버전 확인 중...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다
    echo Python 3.9 이상을 다운로드하고 설치해주세요:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% 확인됨

:: Python 버전 검증 (간단한 방법)
python -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python 3.9 이상이 필요합니다 (현재: %PYTHON_VERSION%)
    pause
    exit /b 1
)

:: 시스템 의존성 확인
echo.
echo 🔧 시스템 의존성 확인 중...

:: FFmpeg 확인
ffmpeg -version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ FFmpeg가 설치되지 않음
    echo.
    echo 📋 FFmpeg 설치 방법:
    echo 1. https://ffmpeg.org/download.html 에서 Windows 빌드 다운로드
    echo 2. 압축 해제 후 bin 폴더를 시스템 PATH에 추가
    echo 3. 또는 Chocolatey 사용: choco install ffmpeg
    echo.
    echo 계속 진행하려면 아무 키나 누르세요...
    pause >nul
) else (
    echo ✅ FFmpeg 설치됨
)

:: Java 확인
java -version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️ Java가 설치되지 않음 (한국어 처리 기능 제한)
    echo.
    echo 📋 Java 설치 방법:
    echo https://www.oracle.com/java/technologies/downloads/
    echo 또는 OpenJDK: https://adoptium.net/
) else (
    echo ✅ Java 설치됨
)

:: 가상 환경 설정
echo.
echo 🐍 가상 환경 설정 중...

if not exist "venv" (
    echo 가상 환경 생성 중...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo ❌ 가상 환경 생성 실패
        pause
        exit /b 1
    )
) else (
    echo ✅ 가상 환경이 이미 존재함
)

:: 가상 환경 활성화
echo 가상 환경 활성화...
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo ❌ 가상 환경 활성화 실패
    pause
    exit /b 1
)

:: pip 업그레이드
echo pip 업그레이드...
python -m pip install --upgrade pip >nul 2>&1

echo ✅ 가상 환경 설정 완료

:: Python 패키지 설치
echo.
echo 📦 Python 패키지 설치 중...

if exist "requirements.txt" (
    echo requirements.txt에서 패키지 설치 중...
    pip install -r requirements.txt
    if %errorLevel% neq 0 (
        echo ⚠️ 일부 패키지 설치 실패, 개별 설치 시도 중...
        goto :individual_install
    ) else (
        echo ✅ 패키지 설치 완료
        goto :after_install
    )
) else (
    echo ⚠️ requirements.txt를 찾을 수 없습니다
    goto :individual_install
)

:individual_install
echo.
echo 🔧 필수 패키지 개별 설치 중...
pip install Flask==3.0.0 beautifulsoup4==4.12.2 requests pandas numpy lxml scikit-learn

echo.
echo 🎨 선택적 패키지 설치 중...
pip install spotipy praw vaderSentiment textblob nltk
:: 일부 실패해도 계속 진행

:after_install

:: 환경변수 템플릿 생성
echo.
echo 📝 환경변수 템플릿 생성 중...

if not exist ".env" (
    echo # Music Merger Project 환경변수 > .env.template
    echo # API 키들을 설정하세요 >> .env.template
    echo. >> .env.template
    echo # Last.fm API >> .env.template
    echo LASTFM_API_KEY=your_lastfm_api_key_here >> .env.template
    echo LASTFM_API_SECRET=your_lastfm_secret_here >> .env.template
    echo. >> .env.template
    echo # Spotify API >> .env.template
    echo SPOTIFY_CLIENT_ID=your_spotify_client_id_here >> .env.template
    echo SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here >> .env.template
    echo. >> .env.template
    echo # YouTube API >> .env.template
    echo YOUTUBE_API_KEY=your_youtube_api_key_here >> .env.template
    echo. >> .env.template
    echo # Reddit API >> .env.template
    echo REDDIT_CLIENT_ID=your_reddit_client_id_here >> .env.template
    echo REDDIT_CLIENT_SECRET=your_reddit_client_secret_here >> .env.template
    echo REDDIT_USER_AGENT=MusicTrendAnalyzer/1.0 >> .env.template
    
    echo ✅ 환경변수 템플릿 생성됨: .env.template
    echo 💡 .env.template을 .env로 복사하고 API 키를 설정하세요
) else (
    echo ✅ .env 파일이 이미 존재함
)

:: 설치 검증
echo.
echo 🔍 설치 검증 중...

python -c "
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

if %errorLevel% neq 0 (
    echo ⚠️ 일부 모듈 로드 실패
) else (
    echo ✅ 설치 검증 완료
)

:: 테스트 실행
echo.
echo 🧪 기본 테스트 실행 중...

if exist "test_new_chart_apis.py" (
    timeout /t 30 python test_new_chart_apis.py >nul 2>&1
    if %errorLevel% neq 0 (
        echo ⚠️ 일부 테스트 실패 (API 키 미설정 가능)
    )
) else (
    echo ⚠️ 테스트 파일을 찾을 수 없습니다
)

:: 완료 메시지
echo.
echo 🎉 설치 완료!
echo ==================================================
echo 다음 단계:
echo 1. venv\Scripts\activate.bat     (가상 환경 활성화)
echo 2. copy .env.template .env       (환경변수 파일 생성)
echo 3. .env 파일에 API 키 설정
echo 4. python app.py                 (앱 실행)
echo 5. http://localhost:5000 접속
echo.
echo 💡 팁:
echo - FFmpeg 설치가 필요한 경우 관리자 권한으로 재실행하세요
echo - API 키 발급 방법은 SETUP_GUIDE.md를 참조하세요
echo.

pause