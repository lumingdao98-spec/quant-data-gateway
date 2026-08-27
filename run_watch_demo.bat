@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
call "%~dp0python_runtime.bat" main.py watch 300750 600519 000001 --interval 5
set "EXIT_CODE=%ERRORLEVEL%"
pause
exit /b %EXIT_CODE%
