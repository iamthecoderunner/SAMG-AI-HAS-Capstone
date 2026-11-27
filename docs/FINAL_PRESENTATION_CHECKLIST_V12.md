# Last-mile submission and presentation checklist

## Ready in v12 code
- [x] End-to-end application with signed local webhook and persistent ticket DB
- [x] Real local LLM invocation path and semantic retrieval verified in prior user-provided screenshots
- [x] Structured citations, source validation, tool calling, RBAC and audit
- [x] Self-reported answer resolution feedback and dashboard counters
- [x] Source-chunk ingestion and revisioning, prompt/data separation
- [x] Automated RAG benchmark runner and manual evaluation protocol
- [x] 20-minute slides + 5-minute Q&A and a defense runbook

## Requires student-side execution/identity; cannot be faked by the build environment
- [ ] Replace role placeholders with actual team names and confirm speaking roles
- [ ] Open consolidated v12 and rerun live 9-check Ollama verifier; save latest PASS JSON
- [ ] Run 6-case real RAG benchmark; disclose actual results and manually score faithfulness
- [ ] Verify browser UI after v12 update, especially Yes/No resolution feedback and dashboard
- [ ] If actual Docker deployment is mandated, run `docker compose build && docker compose up` and capture result (Docker unavailable here)
- [ ] Capture final screenshots with the defense laptop and review for sensitive information
- [ ] Upload to authorized repository and submit link per the professor's instructions

**Not proven:** external production deployment, real password resets, real time-to-resolution savings, enterprise-grade pen test. Do not claim these.
