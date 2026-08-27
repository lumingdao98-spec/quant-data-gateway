@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist "%~dp0.venv\Scripts\python.exe" (
    call "%~dp0python_runtime.bat" -m venv .venv
    if errorlevel 1 goto failed
)
"%~dp0.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
"%~dp0.venv\Scripts\python.exe" -m pip install -r requirements_full.txt
if errorlevel 1 goto failed
echo Installation completed. Use run_api_8001.bat to start the platform.
pause
exit /b 0

:failed
echo Installation failed. Review the error above.
pause
exit /b 1
