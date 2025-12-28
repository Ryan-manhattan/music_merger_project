@echo off
chcp 65001 >nul
title OFF THE COMMUNITY Server

echo.
echo ========================================
echo   OFF THE COMMUNITY 서버 시작
echo ========================================
echo.

:: 프로젝트 루트 디렉토리로 이동
cd /d "%~dp0\.."

:: 현재 디렉토리 확인
echo [INFO] 작업 디렉토리: %CD%
echo.

:: .env 파일 확인
if not exist ".env" (
    echo [WARNING] .env 파일이 없습니다.
    echo [WARNING] .env.example을 참고하여 .env 파일을 생성해주세요.
    echo.
    if exist ".env.example" (
        echo [INFO] .env.example 파일을 복사하여 .env를 만드시겠습니까? (Y/N)
        set /p create_env="> "
        if /i "%create_env%"=="Y" (
            copy ".env.example" ".env" >nul
            echo [OK] .env 파일이 생성되었습니다. 필요한 값들을 채워주세요.
            echo.
        )
    )
)

:: 가상환경 확인 및 활성화
if exist "venv_win\Scripts\activate.bat" (
    echo [INFO] Windows 가상환경 활성화 중...
    call venv_win\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [INFO] 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] 가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다.
)

echo.

:: Python 버전 확인
python --version
if errorlevel 1 (
    echo [ERROR] Python이 설치되어 있지 않거나 PATH에 없습니다.
    echo [ERROR] Python을 설치하고 PATH에 추가해주세요.
    pause
    exit /b 1
)

echo.

:: 필요한 패키지 확인 (선택적)
echo [INFO] 필요한 패키지 확인 중...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [WARNING] Flask가 설치되어 있지 않습니다.
    echo [INFO] requirements.txt에서 패키지를 설치하시겠습니까? (Y/N)
    set /p install_packages="> "
    if /i "%install_packages%"=="Y" (
        echo [INFO] 패키지 설치 중...
        pip install -r requirements.txt
        echo.
    )
)

echo.
echo ========================================
echo   서버 시작
echo ========================================
echo.
echo [INFO] 브라우저에서 http://localhost:5000 에 접속하세요
echo [INFO] 서버를 중지하려면 Ctrl+C를 누르세요
echo.

:: 환경변수 설정 (선택적)
if exist ".env" (
    echo [INFO] .env 파일을 로드합니다.
)

:: Flask 앱 실행
python app.py

:: 실행 완료 메시지
echo.
echo ========================================
echo   서버가 종료되었습니다
echo ========================================
echo.
echo [INFO] 문제가 발생했다면:
echo   - .env 파일의 SUPABASE_URL, SUPABASE_KEY가 올바른지 확인하세요
echo   - 명령 프롬프트에서 'python app.py'를 직접 실행해보세요
echo.

:: 터미널 창 유지
pause

