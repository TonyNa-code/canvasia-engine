@echo off
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 tools\ci\github_status.py %*
) else (
  python tools\ci\github_status.py %*
)

if errorlevel 1 pause
