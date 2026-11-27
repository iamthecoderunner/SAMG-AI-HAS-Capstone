# AI-HAS v12 — Submission readiness and rubric traceability

**Date:** 25 November 2026. **Authoritative source:** supplied *Capstone Project Specification*, pages 1–5. **Status:** deployable for supervised LOCAL demonstration, **not** an enterprise production release.

> **RCTC:** Role = L1 IT helpdesk; Context = approved SOPs + authenticated user + bounded APIs; Task = cited guidance, validated ticketing, simulated approval workflow, escalation and reporting; Control = no invented sources/unsafe privilege execution/false results/secrets. The application enforces important controls in the backend in addition to the prompts.

## Rubric-by-rubric deliverables

| Official rubric | Weight | Implementation & evidence | Release qualification |
|---|---:|---|---|
| Core AI/RAG | 25% | Ollama Qwen3 + nomic-embed-text + ChromaDB, source citations with backend validation, ingestion/chunking/revisioning. Student-provided Windows screenshot demonstrates `semantic+ollama` VPN answer and citation `[1]`; nine-check live verifier reported all PASS. | **Implemented + user-verified for a small synthetic SOP corpus.** Broader live evaluation and independent faithfulness review still needed. |
| Software engineering/automation | 20% | FastAPI, SQLite, session roles, frontend, real LLM-proposed ticket function, validated execution, idempotency, HMAC-signed HTTP webhook and receiver, retries, human escalation. | Real external HTTP webhook verified locally; actual privileged account provisioning is **simulated**. Jira/ServiceNow integration not established; specification names them as options. |
| Governance/security/guardrails | 15% | RBAC, audit, content screening, PII minimization, approval-gate integrity/expiry, anti-replay, secret-free demo packaging. | Classroom controls only; no production penetration test, enterprise IdP, or managed secrets. Public production mode deliberately blocked. |
| Evaluation/testing | 15% | pytest regression, HTTP/restart/persistence, signed-webhook smoke, 22-case synthetic lexical retrieval evaluation, 60-request small-load local benchmark, isolated 9-check Windows Ollama verifier. **v12 adds self-reported resolution feedback and live 6/22-case RAG benchmark runner.** | Tests run on packaging host are not Ollama inference tests. v12 live benchmark and human faithfulness evaluation remain unmeasured until executed on Windows. No fabricated MTTR improvement. |
| Technical documentation | 15% | README, architecture diagrams, API `/docs`, security notes, implementation/ops runbook, test evidence, evaluation guide, requirements matrix, release checklist. | Setup validated for local demo, not remote HTTPS. Docker config exists but cannot be certified without an actual Docker build. |
| Live defense | 10% | Time-coded 20-min slide deck, 5-min Q&A, live demo scripts, recorded screenshots, backup plan, examiner questions. | Presenter must run the live demonstration and provide team names. |

## Concrete run-time cases and what they prove

1. **Cited VPN answer:** actual Ollama generation plus Chroma context and valid citation; one observed response 2,056 ms in student screenshot. This is **one observation**, not representative mean/p95 latency.
2. **Unsupported query:** model refuses/abstains and offers human escalation. Demonstrates bounded scope; do not claim the model never hallucinates.
3. **LLM tool call:** real local model proposes ticket creation; FastAPI validates and saves it. A real privileged password reset is not performed.
4. **Ticket idempotency:** repeated request ID returns the original ticket, preventing duplicate creation.
5. **Approval workflow:** role-restricted, signed? **No: approval is session/RBAC-gated and digest-checked, not cryptographically signed.** This distinction matters for the defense.
6. **Signed webhook:** HMAC on requests to an independent sandbox receiver, retries and delivery log. Do not imply n8n/Jira was deployed.
7. **Feedback:** user can mark answered sessions as resolved/not resolved. Dashboard shows self-reported counts/rates; **not proof of ticket deflection**.

## Readiness classification

- **Ready now:** local supervised defense if models are preloaded, accounts work, and the live verifier is rerun.
- **Needs last-mile local confirmation:** `RUN_LIVE_RAG_EVALUATION_WINDOWS.bat` (quick 6-case benchmark); the 9-check verifier PASS report copied from Windows; Docker build if professor explicitly requests a container demonstration.
- **Not established:** quantitative human-judged faithfulness at scale, reduction in real MTTR, enterprise ticket deflection, public HTTPS hosting, actual identity provisioning, production disaster recovery, independent penetration test.

## Before handing in

- [ ] Fill in real team member names and roles on slides 1–2 (do not invent them).
- [ ] Start Ollama and v12, confirm live `semantic+ollama` answer, ticket tool, RBAC and dashboard.
- [ ] Save v12 `CHECK_FREE_AI_WINDOWS.bat` PASS JSON from actual defense laptop (`docs/evidence/local_ai_verification.json`).
- [ ] Run the new 6-case live benchmark and save JSON; disclose failed cases if present.
- [ ] Capture one screenshot each of live answer, tool ticket, stored ticket, agent review, dashboard and verification status.
- [ ] Do not submit `.env`, user database, Chroma cache, `.venv` or API credentials.
- [ ] Rehearse the timed presentation and Q&A using `docs/DEFENSE_RUNBOOK_25_MIN.md`.
