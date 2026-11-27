# AI-HAS v12 — Windows demo setup and user guide

## Setup on a 16 GB Windows computer

1. Install and open Ollama. Confirm `ollama list` includes `qwen3:4b` and `nomic-embed-text`; if not, the starter can download them.
2. Extract v12 to a NEW folder. Keep your working v11 installation as backup.
3. Copy only your private `.env` and `aihas.db` from the previously working folder into v12, with optional `chroma` folder. Do not send these files to anyone. Stop old server before v12 startup.
4. Double-click `START_FREE_AI_WINDOWS.bat`. Keep terminal open; browse to `http://127.0.0.1:8000`.
5. Use employee account to ask for VPN troubleshooting; confirm `semantic+ollama` and correct SOP citation. Submit Yes/No feedback and show the agent's dashboard counter.
6. To test the real model independently, double-click `CHECK_FREE_AI_WINDOWS.bat`; preserve generated `docs/evidence/local_ai_verification.json` from your actual laptop.
7. To test a wider sample, double-click `RUN_LIVE_RAG_EVALUATION_WINDOWS.bat` (6 questions), or run `python scripts/evaluate_local_rag.py --full` (22 questions) in the project venv. Retain all failed cases and review them.

## Roles and UI

- **Employee:** chat with citations, request helpdesk ticket, inspect own tickets/requests, submit one resolution feedback per answered chat.
- **Agent:** all above plus agent queue/status updates, history, simulated approval/denial, dashboard.
- **Admin:** agent abilities plus KB upload/edit/delete, audit trail and outbound webhook delivery ledger.

## Demo shutdown and restart

- Press `Ctrl+C` in the AI-HAS terminal. Keep Ollama open only when actively testing.
- `aihas.db` stores operational records; `chroma` stores vector indexes. Make a copy of both only after stopping services. Do not distribute them with code.
- If the app is not responding, check `http://127.0.0.1:8000/api/health`, Python terminal errors and Ollama app status; do not delete your database blindly.
- If you receive a safe SOP extract rather than `semantic+ollama`, record that distinction and use the verifier report to diagnose provider behavior.

## Docker notes (NOT verified in this build environment)

- The project has Dockerfile and Docker Compose configuration for a controlled sandbox demonstration. Docker CLI was not available on the packaging host.
- If your professor requires a containerized demonstration, install Docker Desktop and, from the project folder, execute `docker compose build` then `docker compose up` only after reviewing `docker-compose.yml` and `.env` settings. The Compose file defaults to `OLLAMA_BASE_URL=http://host.docker.internal:11434` for host Ollama and `INSTALL_SEMANTIC=1` to install ChromaDB; verify that your Ollama host actually accepts container requests, and capture the build and health-check outputs. These settings have NOT been executed in this packaging environment.
- **Do not publish demo mode or default accounts to a public network.** Production deployment is deliberately blocked by the application pending enterprise controls.

## What not to upload

`.env`, API keys, `.venv`, `aihas.db`, active `chroma` directory, personal user data, live private audit records, and local password screenshots. Submission ZIP already excludes them.
