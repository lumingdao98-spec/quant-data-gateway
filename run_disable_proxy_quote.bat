@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set QUANT_DISABLE_PROXY=1
call "%~dp0python_runtime.bat" main.py quote 300750 600519 000001 --force
set "EXIT_CODE=%ERRORLEVEL%"
pause
exit /b %EXIT_CODE%
