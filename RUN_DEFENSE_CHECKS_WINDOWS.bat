@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo BLOCKED: Run START_FREE_AI_WINDOWS.bat to install the environment.
 pause
 exit /b 2
)
echo [1/4] Python regression tests
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 echo FAIL: Python test suite

echo [2/4] Local HTTP integration and restart checks
".venv\Scripts\python.exe" scripts\http_smoke.py
if errorlevel 1 echo FAIL: HTTP smoke

echo [3/4] Signed webhook receiver test
".venv\Scripts\python.exe" scripts\webhook_smoke.py
if errorlevel 1 echo FAIL: webhook smoke

echo [4/4] Actual Ollama and Chroma live verification
".venv\Scripts\python.exe" scripts\verify_local_ai.py
if errorlevel 1 echo FAIL/BLOCKED: live Ollama verification - see docs\evidence\local_ai_verification.json

echo Review each individual result. Never treat this summary as a guarantee of production readiness.
pause
