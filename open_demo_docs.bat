\
@echo off
setlocal
cd /d "%~dp0"
echo Opening key demo docs...
start "" "docs\demo_readiness_checklist.md"
start "" "docs\linkedin_post.md"
start "" "docs\architecture.md"
start "" "README.md"
endlocal
