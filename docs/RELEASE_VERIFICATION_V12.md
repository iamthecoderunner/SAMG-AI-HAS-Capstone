# v12 — Recorded release verification (packaging environment)

**Date:** 2026-11-25. All checks were executed on the packaging host using synthetic accounts and a disposable SQLite database, not on the student's external environment unless explicitly marked.

| Command / evidence | Measured result | Scope and important limitations |
|---|---|---|
| `python -m pytest -q` | **95 passed**, 0 failed | Automated unit and integration fixtures; local provider tests use test doubles; not a live Ollama quality test |
| `python scripts/http_smoke.py` | **12 passed**, including real Uvicorn, ticket and approval persistence, new user resolution feedback and restart | Loopback FastAPI and SQLite; no real LLM or external network |
| `python scripts/webhook_smoke.py` | **PASS**: HMAC signature, independent receiver, replay/expiry rejection, no duplicate notification | Two independent local HTTP servers; no n8n/Jira or production webhook |
| `python scripts/evaluate_retrieval.py` | **22/22 passed**; recall@3=1.0 on 18 supported cases; unsupported abstention=1.0 on 4 cases | **TF-IDF lexical** only on 6 synthetic SOPs; not true semantic vector or LLM faithfulness |
| `python scripts/load_smoke.py` | **60/60 passed**, 6 workers, p50 ~10.7 ms, p95 ~63.7 ms | SMALL local offline lexical load, NOT live Ollama inference or enterprise throughput |
| `python scripts/evaluate_local_rag.py --quick` | **NOT YET RUN HERE** | Requires real Ollama and Chroma on the student's Windows machine; script included; do not invent a score |
| v11 real user screenshot + terminal | **Prior user evidence:** 9 live checks PASS, live VPN `semantic+ollama` and citation `[1]`, one 2,056 ms response | Evidence provided in conversation; model still requires re-verification after applying v12 code on the defense laptop |
| `docker compose ...` | **NOT TESTED HERE** | No Docker executable in packaging environment, no public deployment certification |

## What changed relative to v11

- New one-response-per-answer **employee resolution feedback** endpoint (owner-only with idempotent one-time record and audit).
- Metrics distinguish self-reported resolved feedback from answered-chat rate and actual MTTR improvement.
- Updated front-end feedback buttons and dashboard labels.
- 6-case quick / 22-case full **real local Ollama/Chroma evaluation runner** with case-level results and explicit missing-faithfulness caveat.
- Expanded actual HTTP smoke coverage to 12 checks, including feedback persistence after restart.
- 25-minute timed defense deck with presenter notes, architecture, live evidence images and Q&A appendix.
- Updated security/QA, API, schema, deployment, evaluation and rubric evidence documentation.

**Release decision:** GO for a supervised *local academic demonstration*, provided the user's own v12 Ollama verification passes; NO-GO for unattended enterprise production deployment.
