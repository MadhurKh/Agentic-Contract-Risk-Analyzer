@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ------------------------------------------------------------
REM Agentic Contract Risk Analyzer - CLI Export Runner (Windows)
REM Writes:
REM   outputs\latest_demo_run.json
REM   outputs\demo_run_YYYYMMDD_HHMMSS.json
REM Logs:
REM   outputs\export_run.log
REM   outputs\export_error.txt (only if failure)
REM ------------------------------------------------------------

set "REPO_ROOT=%~dp0"
REM remove trailing backslash
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"

cd /d "%REPO_ROOT%"

if not exist "outputs" mkdir "outputs"

set "LOG=outputs\export_run.log"
echo =============================== > "%LOG%"
echo Agentic Contract Risk Analyzer  >> "%LOG%"
echo Repo root: %REPO_ROOT%          >> "%LOG%"
echo Start: %DATE% %TIME%            >> "%LOG%"
echo =============================== >> "%LOG%"

set "PY_EXE="

REM Prefer repo-local virtualenvs
if exist "%REPO_ROOT%\.venv\Scripts\python.exe" set "PY_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
if not defined PY_EXE if exist "%REPO_ROOT%\venv\Scripts\python.exe" set "PY_EXE=%REPO_ROOT%\venv\Scripts\python.exe"

REM If running inside an activated venv, use it
if not defined PY_EXE if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" set "PY_EXE=%VIRTUAL_ENV%\Scripts\python.exe"

REM Fallback to python on PATH
if not defined PY_EXE set "PY_EXE=python"

echo Using Python: %PY_EXE%
echo Using Python: %PY_EXE% >> "%LOG%"

echo.
echo Running export...
echo Running export... >> "%LOG%"

"%PY_EXE%" -u "scripts\run_export_demo.py" --sample --agentic --require-citations --jurisdictions EU AU --out "outputs\latest_demo_run.json" >> "%LOG%" 2>&1

set "EXIT_CODE=%ERRORLEVEL%"

echo. >> "%LOG%"
echo Exit code: %EXIT_CODE% >> "%LOG%"
echo End: %DATE% %TIME% >> "%LOG%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo Export FAILED. See outputs\export_run.log and outputs\export_error.txt
  echo.
  echo Opening outputs folder...
  explorer "%REPO_ROOT%\outputs" >nul 2>&1
  echo.
  echo Press any key to close...
  pause >nul
  exit /b %EXIT_CODE%
)

echo.
echo Export SUCCESS.
echo Wrote: outputs\latest_demo_run.json
echo.
echo Opening outputs folder...
explorer "%REPO_ROOT%\outputs" >nul 2>&1

echo.
echo Press any key to close...
pause >nul
exit /b 0
