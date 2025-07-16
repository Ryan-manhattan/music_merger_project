@echo off
echo Starting Music Merger Server...
echo Server URL: http://localhost:5000
echo.

call venv_win\Scripts\activate.bat
python app.py

pause