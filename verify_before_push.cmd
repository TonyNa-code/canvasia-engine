@echo off
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 tools\ci\local_verify.py --profile standard %*
) else (
  python tools\ci\local_verify.py --profile standard %*
)

if errorlevel 1 pause
