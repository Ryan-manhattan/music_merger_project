@echo off
cd /d %~dp0

echo ================================
echo  Music Merger App Starting...
echo ================================

REM Python 경로 설정
set "PYTHON_EXE=C:\Users\Ryan.김준형\AppData\Local\Programs\Python\Python313\python.exe"

REM Windows 가상환경 생성 (없는 경우)
if not exist "venv_win" (
    echo Creating Windows virtual environment...
    "%PYTHON_EXE%" -m venv venv_win
)

REM 가상환경 활성화
echo Activating virtual environment...
call venv_win\Scripts\activate.bat

REM 의존성 설치
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Flask 앱 실행
echo.
echo Starting web application...
echo Open browser and go to http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ================================

python app.py

echo.
echo Application closed.
pause