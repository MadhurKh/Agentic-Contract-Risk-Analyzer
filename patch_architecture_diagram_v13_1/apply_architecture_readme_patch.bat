@echo off
setlocal enabledelayedexpansion

REM Run from repo root
cd /d "%~dp0.."

echo ============================================
echo Applying Architecture Diagram README patch...
echo Repo: %CD%
echo ============================================

REM Prefer local venv Python if present
if exist ".venv\Scripts\python.exe" (
  set PY=.venv\Scripts\python.exe
) else (
  set PY=python
)

"%PY%" scripts\apply_architecture_readme_patch.py
set RC=%ERRORLEVEL%

if %RC% neq 0 (
  echo.
  echo [WARN] README patch may not have been applied (README not found or already patched).
) else (
  echo.
  echo [OK] README updated with Architecture Diagram section (if not already present).
)

echo.
echo Files added:
echo  - docs\architecture.md
echo  - docs\assets\architecture.png
echo  - docs\assets\architecture.svg
echo  - docs\hiring_manager_pack\4_architecture.md
echo.
pause
