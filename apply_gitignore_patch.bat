@echo off
setlocal enabledelayedexpansion

REM Apply .gitignore append safely (no duplicates)
set REPO_ROOT=%~dp0
cd /d "%REPO_ROOT%"

if not exist ".gitignore" (
  echo Creating .gitignore
  type nul > ".gitignore"
)

if not exist ".gitignore.append" (
  echo ERROR: .gitignore.append not found in repo root.
  echo Press any key to exit...
  pause >nul
  exit /b 1
)

for /f "usebackq delims=" %%L in (".gitignore.append") do (
  set LINE=%%L
  REM Skip empty lines safely
  if "!LINE!"=="" (
    echo.>>".gitignore"
  ) else (
    findstr /c:"%%L" ".gitignore" >nul 2>&1
    if errorlevel 1 (
      echo %%L>>".gitignore"
    )
  )
)

echo.
echo Updated .gitignore successfully.
echo Press any key to exit...
pause >nul
endlocal
