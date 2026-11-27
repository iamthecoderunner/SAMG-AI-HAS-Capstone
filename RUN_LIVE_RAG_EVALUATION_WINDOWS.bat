@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo BLOCKED: Set up the v12 project environment first.
  pause
  exit /b 2
)
".venv\Scripts\python.exe" scripts\evaluate_local_rag.py --quick
if errorlevel 1 (
  echo See docs\evidence\live_rag_evaluation.json for case-by-case outcomes.
) else (
  echo Local RAG benchmark passed all six cases.
)
pause
