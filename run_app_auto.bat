@echo off
chcp 65001 >nul
python main.py api --host 127.0.0.1 --port 8000 --auto-port
pause
