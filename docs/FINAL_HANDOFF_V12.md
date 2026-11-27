# AI-HAS Final Hand-off v12 — Immediate actions

**The complete source and 25-minute defense deck are packaged.** Core app functions retain the locally verified v11 Ollama/Chroma model path; v12 adds resolution feedback, evaluation runner and defense material.

## Start here (Windows)

1. **Do not delete the working v11 app.** Extract v12 to a new folder and stop the old AI-HAS terminal.
2. Copy your existing private `.env`, `aihas.db`, and optional `chroma` folder into v12 `AI-HAS`. Never upload them to a public repository.
3. Keep Ollama running; double-click `START_FREE_AI_WINDOWS.bat` in v12.
4. Confirm a user question shows `semantic+ollama` and the correct SOP source; click **Yes** on the new resolution feedback control and verify that the staff dashboard count increases.
5. Double-click `RUN_DEFENSE_CHECKS_WINDOWS.bat` to repeat the 95-test/12-HTTP/webhook and nine-check live Ollama verification on your own machine.
6. Optional but recommended: `RUN_LIVE_RAG_EVALUATION_WINDOWS.bat` runs 6 actual live Ollama RAG scenarios, saving `docs/evidence/live_rag_evaluation.json`. A failure is evidence of a remaining model-quality problem and must not be concealed.
7. Open the editable **21-slide** `docs/AI-HAS_25_Minute_Defense_v12.pptx`. Replace Member 1–4 role placeholders with actual member names (or adapt to a three-member team), and rehearse the 00:00–25:00 plan in `docs/DEFENSE_RUNBOOK_25_MIN.md`.

## What cannot be certified from this environment

A public HTTPS production deployment, real password reset/provisioning, enterprise identity, an independent penetration test, real enterprise MTTR/deflection gains, and full-scale RAG factual accuracy are not demonstrated. Docker configuration has been prepared, not built here. The official capstone specification focuses on a demonstrable academic system; these production considerations must be disclosed, not misrepresented.
