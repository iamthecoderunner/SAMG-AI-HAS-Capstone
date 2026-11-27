# AI-HAS v12 — Evaluation protocol and interpretation

**Do not equate code-test success with generative AI correctness.** Report each category separately:

1. **Automated software regression:** `python -m pytest -q` (API, RBAC, state transitions, citation validation, idempotency, privacy, controlled approval, retrieval test doubles).
2. **Real local HTTP and persistence:** `python scripts/http_smoke.py`; tests a real Uvicorn process and SQLite across restart; does not use Ollama.
3. **Independent webhook:** `python scripts/webhook_smoke.py`; proves signed two-service HTTP integration, not n8n/ServiceNow.
4. **Synthetic lexical retrieval:** `python scripts/evaluate_retrieval.py` for 18 supported + 4 unsupported cases; TF-IDF only, not vector retrieval, not LLM faithfulness.
5. **Small-load test:** `python scripts/load_smoke.py` with 60 requests/6 workers; does not extrapolate to enterprise concurrency.
6. **Actual local Ollama smoke:** `CHECK_FREE_AI_WINDOWS.bat` with 9 checks; account and model must be working on Windows; preserving the PASS JSON is mandatory.
7. **Actual local RAG benchmark (NEW):** `RUN_LIVE_RAG_EVALUATION_WINDOWS.bat` runs 6 representative questions. For 22 cases: `python scripts/evaluate_local_rag.py --full`. It creates disposable SQLite/Chroma stores and records source-hit rate, cited Ollama answer rate, unsupported abstention, and per-query latency. **A valid citation is NOT automatic proof of faithfulness.**
8. **Manual answer auditing:** Two reviewers compare each of at least 10 live answers with the cited SOPs and score factual support, completeness, and correctness as Yes/No. Keep disagreements and raw scores. Until these reviews are done, faithfulness = `NOT YET MEASURED`.

## How metrics are defined

- **Retrieval hit rate:** applicable cases where the expected SOP title is among returned source titles / applicable cases. Distinct from precision and answer faithfulness.
- **Cited live answer rate:** supported queries answered in `semantic+ollama` mode with valid cited IDs / supported queries. Excludes SOP extract fallback from live LLM generation.
- **Unsupported abstention rate:** unsupported queries that yield no cited answer and return an escalation/out-of-scope outcome / unsupported queries.
- **Human-reviewed answer faithfulness:** number of evaluated answers fully supported by the cited SOPs / number audited. **Must be manually measured**, not inferred from citations alone.
- **Self-reported resolution rate (NEW):** positive Yes responses / all Yes/No responses; small synthetic demo only. Not automatic deflection.
- **Observed ticket resolution time:** resolved ticket's `updated_at` minus `created_at`; local demo sample, not comparative MTTR.
- **Actual MTTR improvement:** `(baseline MTTR - new MTTR)/baseline MTTR`. **NOT MEASURED** without comparable operational baseline and measured intervention group.
- **Actual ticket deflection:** eligible L1 contacts resolved without requiring a human ticket / eligible L1 contacts, with confirmed outcomes and tracked eligibility. **NOT MEASURED** in enterprise operations.

## Fair presentation language

Say: “The 9-check verifier on our demonstration laptop reported PASS for live model citation, Chroma indexing, tool call and storage. We tested 95+ local application checks separately; those are not equivalent to production AI accuracy.”

Do not say: “100% hallucination-free”, “enterprise production ready”, “80% fewer tickets”, “zero security vulnerabilities”, or “measured MTTR reduction” unless supported by an appropriate dataset and reproduced results.
