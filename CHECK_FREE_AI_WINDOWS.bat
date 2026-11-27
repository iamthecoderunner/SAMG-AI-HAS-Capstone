@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo BLOCKED: Run START_FREE_AI_WINDOWS.bat once to install dependencies.
 goto finish
)
".venv\Scripts\python.exe" scripts\verify_local_ai.py --preflight
if errorlevel 1 goto finish
".venv\Scripts\python.exe" scripts\verify_local_ai.py
:finish
echo.
pause
endlocal
