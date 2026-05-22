@echo off
chcp 65001 >nul
call .venv\Scripts\activate
python main.py quote 300750 600519 000001
pause
