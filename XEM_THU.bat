@echo off
cd /d "%~dp0"
echo Dang mo Dink Radar tai http://localhost:8000 ... (dong cua so nay de tat)
start "" http://localhost:8000/index.html
python -m http.server 8000 || py -m http.server 8000
pause
