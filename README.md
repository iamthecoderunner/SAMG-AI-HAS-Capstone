# AI-HAS — Consolidated Local AI Capstone (v11)

**AI-Powered Enterprise Helpdesk & Workflow Automation System**  
**Status:** locally integrated academic prototype; live Ollama/Chroma path demonstrated on a student's Windows laptop; **not** certified as an enterprise production deployment.

> **START HERE:** This document supersedes the older v7/v8 headings in archived documentation. The included source merges the v10 application and v11 structured-citation hotfix. You do **not** need to install earlier v10 or hotfix ZIPs first.

## Quick start — Windows, Ollama, 16 GB RAM

1. Install and run [Ollama](https://ollama.com/download/windows) on Windows.
2. Extract this ZIP into a **new** folder. Stop your previous AI-HAS server with `Ctrl+C`. Keep Ollama running.
3. Copy your privately configured `.env` and `aihas.db` from the **working** AI-HAS installation into this release's `AI-HAS` folder. If present, optionally copy your `chroma` directory. Do not share these files with others or commit them to GitHub.
4. Double-click `START_FREE_AI_WINDOWS.bat` in this folder. The script installs Python dependencies, downloads/validates the local models, runs a live verification and starts the app. Preserve the terminal; open `http://127.0.0.1:8000`.
5. To run the full live verification independently, double-click `CHECK_FREE_AI_WINDOWS.bat`. The script records a JSON report at `docs/evidence/local_ai_verification.json` **on your computer**. Keep the actual PASS report and the screenshot for the defense.
6. Try `How can I troubleshoot VPN issues?`. A live model-generated, cited answer will show `semantic+ollama` and cite the VPN SOP; `semantic+sop_extract_fallback` is a safe fallback but must **not** be counted as model-generated answer verification.

No OpenAI API key or paid service is required for the local Ollama pathway. Qwen3 4B and nomic-embed-text must be installed through Ollama; model downloads, disk space, and adequate RAM are required.

## Verified scope and honest boundaries

- **Live Windows evidence provided by project owner:** terminal reports nine PASS checks for authentication, RAG HTTP, semantic retrieval, Qwen3 cited generation, real Chroma index, Ollama function call, ticket persistence, idempotency and audit. Separate browser screenshot shows `semantic+ollama` with cited VPN SOP and 2,056 ms for one VPN query. These results are **user-provided evidence**, not measurements performed on this packaging host.
- **Verified by packaging host:** 90 local automated tests, 10 loopback HTTP checks, independent two-server signed webhook integration. Offline tests include mocked Ollama responders; the local Python environment did not run Ollama inference.
- **Bounded privileged actions:** Software access and password reset approvals are **simulated** and do not modify real enterprise identities or provision accounts. Human review and backend authorization are required.
- **Not established:** generalized RAG accuracy across production documents, real enterprise MTTR reduction, n8n/Jira production deployment, public HTTPS hosting, penetration testing, disaster recovery, enterprise identity and operational certification.

## Contents

- `app/main.py`, `app/local_ai.py`, `app/static/index.html`: backend, local AI integrations, frontend.
- `scripts/verify_local_ai.py`: isolated real model, semantic index, tool-call and persistence verifier.
- `integrations/sandbox_webhook.py`: independent local signed-webhook receiver.
- `tests/`: regression suite including v11 structured-citation tests.
- `docs/evidence/user_verified_v11_semantic_ollama_vpn.webp`: user-provided browser screenshot of the live cited response.
- `docs/RELEASE_AUDIT_V11.md`: precise rubric traceability, limitations, and remaining manual submission steps.
- `docs/ARCHITECTURE.md`, `docs/DEFENSE_GUIDE.md`: architectural and defense preparation materials. Older v7/v8 docs and decks are historical and may describe past verification states.

## Test locally (without Ollama)

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Before distributing the code, do **not** include the `.env`, `.venv`, `aihas.db` or live `chroma` directories. The project is designed for a local academic demo, not unrestricted public exposure.

---

## v12 defense and evaluation update (25 November 2026)

**This section supersedes the archived v11 release notes for defense preparation.** Core Ollama + Chroma semantic RAG and model-proposed ticket execution remain intact. v12 adds employee Yes/No answer-resolution feedback (stored once per answered conversation), dashboard reporting of that feedback, a live 6/22-case RAG benchmark runner, and an exact 20-minute presentation + 5-minute Q&A deck.

**Single project package:** use the consolidated v12 ZIP. Extract into a **new** directory and preserve your working v11 installation; copy only your private `.env` and `aihas.db`, and optionally `chroma`, into v12. Do not copy any secrets into a public repository. Start Ollama, then double-click `START_FREE_AI_WINDOWS.bat`.

**Defense and evaluation commands (Windows):**

- `CHECK_FREE_AI_WINDOWS.bat` — reruns the original 9-check real model/vector/function-call verifier (preserve PASS JSON).
- `RUN_LIVE_RAG_EVALUATION_WINDOWS.bat` — evaluates 6 supported/unsupported questions with real Ollama; generates `docs/evidence/live_rag_evaluation.json`. A FAIL is diagnostic evidence and must be reported, not hidden.
- `RUN_DEFENSE_CHECKS_WINDOWS.bat` — tests the local Python/HTTP/webhook stack and real AI verifier in sequence.
- `docs/AI-HAS_25_Minute_Defense_v12.pptx` — exactly matches the 00:00–25:00 presentation time blocks, with editable member labels and speaker notes.
- `docs/DEFENSE_RUNBOOK_25_MIN.md` — minute-by-minute demo and panel answers.
- `docs/SUBMISSION_READINESS_V12.md`, `docs/RELEASE_VERIFICATION_V12.md`, `docs/EVALUATION_PROTOCOL_V12.md`, `docs/ARCHITECTURE_AND_WORKFLOW_V12.md`, `docs/DATABASE_AND_API_V12.md`, `docs/SECURITY_AND_QA_V12.md` — rubric, implementation and assessment support.

**Important evidence boundary:** the nine-check live v11 result was observed on the student's Windows computer; v12 packaging-host tests are distinct. The new v12 multi-question live RAG evaluation and public Docker/HTTPS deployment remain unverified until actually executed. Human-approved access and password-reset actions remain simulation only.

**Document index:** `docs/DOCUMENT_INDEX_V12.md` lists the current authoritative technical and defense documents. Historical materials are not current release claims.
