@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
call "%~dp0python_runtime.bat" main.py api --host 127.0.0.1 --port 8001
set "EXIT_CODE=%ERRORLEVEL%"
pause
exit /b %EXIT_CODE%
