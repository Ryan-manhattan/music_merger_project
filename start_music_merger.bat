@echo off
chcp 65001 >nul
title Music Merger Server

echo 🎵 Music Merger 서버를 시작합니다...
echo.

:: 현재 스크립트 디렉토리로 이동
cd /d "%~dp0"

:: 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo 📦 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다.
)

:: Python 버전 확인
python --version
echo 🔧 필요한 패키지 설치 확인 중...
echo.

:: Flask 앱 실행
echo 🚀 Music Merger 서버 시작!
echo 📍 브라우저에서 http://localhost:5000 에 접속하세요
echo 🛑 서버를 중지하려면 Ctrl+C를 누르세요
echo.

:: Flask 앱 실행
python app.py

:: 실행 완료 메시지
echo.
echo 🎵 Music Merger 서버가 종료되었습니다.
echo ❓ 문제가 발생했다면 명령 프롬프트에서 'python app.py'를 직접 실행해보세요.
echo.

:: 터미널 창 유지
pause