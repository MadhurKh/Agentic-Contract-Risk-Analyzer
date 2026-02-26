@echo off
setlocal

set REPO_ROOT=%~dp0
cd /d "%REPO_ROOT%"

REM Prefer venv python if present
set PY=
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe
if "%PY%"=="" set PY=python

echo Creating demo bundle...
%PY% scripts\make_demo_bundle.py

echo.
echo Press any key to exit...
pause >nul
endlocal
