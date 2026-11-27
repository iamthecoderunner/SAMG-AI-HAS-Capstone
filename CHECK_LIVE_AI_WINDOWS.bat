@echo off
setlocal
cd /d "%~dp0"
echo.
echo AI-HAS external AI verification (safe / isolated test database)
echo Never paste your API key into a terminal or this chat.
echo.
if not exist ".env" (
  echo BLOCKED: .env is missing. Start the local app first, then add your private OpenAI API key.
  goto finish
)
if not exist ".venv\Scripts\python.exe" (
  echo BLOCKED: .venv is missing. Start the local app first.
  goto finish
)
".venv\Scripts\python.exe" -m pip install -r requirements-semantic.txt
if errorlevel 1 (
  echo BLOCKED: Semantic Python package installation failed.
  goto finish
)
".venv\Scripts\python.exe" scripts\release_readiness.py
".venv\Scripts\python.exe" scripts\verify_live_ai.py --preflight
if errorlevel 1 (
  echo BLOCKED: See the preflight output. No live AI result can be claimed.
  goto finish
)
".venv\Scripts\python.exe" scripts\verify_live_ai.py
if errorlevel 1 (
  echo The live integration did not pass. See docs\evidence\live_ai_verification.json if present.
  goto finish
)
echo PASS: live integration was tested. Record only that supported scope; do not claim production security.
:finish
echo.
pause
endlocal
