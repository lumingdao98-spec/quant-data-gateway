@echo off
setlocal

set "PROJECT_ROOT=%~dp0"

if exist "%PROJECT_ROOT%.venv\Scripts\python.exe" goto project_venv

where py >nul 2>nul
if not errorlevel 1 (
    py -3.11 -c "import sys" >nul 2>nul
    if not errorlevel 1 goto py311_launcher
)

if exist "D:\software\python\python.exe" goto d_drive_python

where py >nul 2>nul
if not errorlevel 1 goto py_launcher

where python >nul 2>nul
if not errorlevel 1 goto path_python

if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" goto codex_python

echo [ERROR] No usable Python runtime was found.
echo Install Python 3.11 or newer, or restore the Windows py launcher.
exit /b 9009

:project_venv
"%PROJECT_ROOT%.venv\Scripts\python.exe" %*
exit /b %ERRORLEVEL%

:d_drive_python
"D:\software\python\python.exe" %*
exit /b %ERRORLEVEL%

:py311_launcher
py -3.11 %*
exit /b %ERRORLEVEL%

:py_launcher
py -3 %*
exit /b %ERRORLEVEL%

:path_python
python %*
exit /b %ERRORLEVEL%

:codex_python
"%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" %*
exit /b %ERRORLEVEL%
