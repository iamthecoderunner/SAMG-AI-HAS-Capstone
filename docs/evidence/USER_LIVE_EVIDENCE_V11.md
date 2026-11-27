# User-provided local AI verification evidence

1. On 25 Nov 2026, user supplied a Windows terminal screenshot reporting `PASS:` for `login`, `rag_http`, `semantic_retrieval`, `ollama_cited_generation`, `real_chroma_index`, `ollama_function_call`, `ticket_persistence`, `idempotency`, and `audit`. A `local_ai_verification.json` file containing this *latest* PASS was not uploaded at packaging time. Earlier uploaded FAIL JSON is not reused as PASS evidence.
2. The subsequent browser screenshot `user_verified_v11_semantic_ollama_vpn.webp` shows the user asking `How can I troubleshoot VPN issues?`. The reply is a cited VPN troubleshooting answer `[1]`; UI reports `semantic+ollama · 2056 ms · answered`. The screenshot is evidence of this **specific run**, not a generalized accuracy/latency guarantee.
3. The locally packaged code passed 90 tests, real local HTTP smoke 10/10 and signed-webhook smoke. These are distinct from the user-provided live model evidence.

For final assessment, retain the actual nine-check PASS JSON generated on the student's computer and provide its full report to the examiner if required. Do not copy or share the `.env` file, database with personal data, secrets, or session cookies.
