@echo off
chcp 65001 >nul
call .venv\Scripts\activate
python main.py watch 300750 600519 000001 --interval 5
pause
