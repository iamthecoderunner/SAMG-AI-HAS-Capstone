@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run START_AI_HAS_WINDOWS.bat once to create Python environment.
 pause
 exit /b 1
)
echo Running isolated API, security and integration regression tests...
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 goto failure
echo Running lexical retrieval evaluation (synthetic documents only)...
".venv\Scripts\python.exe" scripts\evaluate_retrieval.py
if errorlevel 1 goto failure
echo Running real local HTTP and persistence checks...
".venv\Scripts\python.exe" scripts\http_smoke.py
if errorlevel 1 goto failure
echo Running independent signed webhook integration...
".venv\Scripts\python.exe" scripts\webhook_smoke.py
if errorlevel 1 goto failure
echo Running small-load HTTP test (not production performance)...
".venv\Scripts\python.exe" scripts\load_smoke.py
if errorlevel 1 goto failure
echo All selected local checks returned successful exit codes.
echo For real external AI verification see docs\LIVE_AI_VERIFICATION.md.
pause
exit /b 0
:failure
echo A test failed. Copy the error above (excluding secrets) for investigation.
pause
exit /b 1
