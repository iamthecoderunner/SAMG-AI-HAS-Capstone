@echo off
setlocal
cd /d "%~dp0"
echo.
echo ====================================================
echo AI-HAS Academic Demo - Local Startup
 echo ====================================================
echo.
if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating isolated Python environment...
    py -3 -m venv .venv
    if errorlevel 1 goto failure
)
echo [2/4] Installing or checking Python packages...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failure
if not exist ".env" (
    echo [3/4] Initializing unique local credentials...
    ".venv\Scripts\python.exe" scripts\bootstrap_demo.py
    if errorlevel 1 goto failure
    echo.
    echo IMPORTANT: Save the three credentials shown above privately.
) else (
    echo [3/4] Reusing your existing local .env.
)
echo [4/4] Starting the application at http://127.0.0.1:8000
echo.
echo Keep this window open. To stop, press Ctrl+C.
echo No credentials are sent to ChatGPT.
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000
if errorlevel 1 goto failure
goto end
:failure
echo.
echo START FAILED. Capture or copy the error above; do not send any secrets.
pause
:end
endlocal
