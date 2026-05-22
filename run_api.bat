@echo off
chcp 65001 >nul
call .venv\Scripts\activate
python main.py api --host 127.0.0.1 --port 8000
pause
