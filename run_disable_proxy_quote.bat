@echo off
chcp 65001 >nul
set QUANT_DISABLE_PROXY=1
call .venv\Scripts\activate
python main.py quote 300750 600519 000001 --force
pause
