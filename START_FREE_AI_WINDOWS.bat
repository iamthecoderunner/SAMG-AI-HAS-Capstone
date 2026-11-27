@echo off
setlocal
cd /d "%~dp0"
echo.
echo AI-HAS Local AI - Zero Paid API Setup
 echo ==============================================
echo.
where ollama >nul 2>&1
if errorlevel 1 (
 echo BLOCKED: Install Ollama for Windows first:
 echo https://ollama.com/download/windows
 goto failure
)
if not exist ".venv\Scripts\python.exe" (
 echo [1/7] Creating Python environment...
 py -3 -m venv .venv
 if errorlevel 1 goto failure
)
echo [2/7] Installing Python packages, including ChromaDB...
".venv\Scripts\python.exe" -m pip install -r requirements-semantic.txt
if errorlevel 1 goto failure
if not exist ".env" (
 echo [3/7] Creating unique local demo credentials...
 ".venv\Scripts\python.exe" scripts\bootstrap_demo.py
 if errorlevel 1 goto failure
 echo SAVE THE PRINTED PASSWORDS PRIVATELY.
) else (
 echo [3/7] Preserving existing .env and passwords.
)
echo [4/7] Configuring free Ollama provider...
".venv\Scripts\python.exe" scripts\configure_free_ai.py
if errorlevel 1 goto failure
echo [5/7] Downloading chat model if needed ^(about 2.5 GB^)...
ollama pull qwen3:4b
if errorlevel 1 goto failure
echo [6/7] Downloading local embedding model ^(about 274 MB^)...
ollama pull nomic-embed-text
if errorlevel 1 goto failure
echo [7/7] Verifying local AI; this may be slow on first run...
".venv\Scripts\python.exe" scripts\verify_local_ai.py --preflight
if errorlevel 1 goto failure
".venv\Scripts\python.exe" scripts\verify_local_ai.py
if errorlevel 1 (
 echo WARNING: The local AI test did not PASS. See the error status, never share secrets.
 echo The application can start but local AI may be unavailable.
)
echo.
echo Starting AI-HAS on http://127.0.0.1:8000
".venv\Scripts\python.exe" -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000
if errorlevel 1 goto failure
goto finish
:failure
echo.
echo SETUP BLOCKED / FAILED. Capture the nonsecret error above and send it to ChatGPT.
pause
:finish
endlocal
