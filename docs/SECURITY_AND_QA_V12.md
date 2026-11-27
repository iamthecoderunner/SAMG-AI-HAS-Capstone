# AI-HAS v12 — Security review, adversarial cases and test plan

## Boundaries and non-negotiable invariants

1. An anonymous client cannot read tickets or use protected APIs.
2. An employee cannot update another user's ticket or invoke agent/admin functions.
3. An unauthorized model tool suggestion does not mutate the database.
4. Unknown SOP/citation failures cannot silently become verified answers.
5. Duplicate ticket request IDs must return an existing ticket or reject conflicts.
6. Expired, altered or already-decided approvals may not be accepted.
7. Demo account passwords and secret settings never belong in the release ZIP.
8. Failed external webhooks are tracked and retried with bounds; no false claim of successful delivery.

## Test matrix

| Test | Method | Expected control | Evidence |
|---|---|---|---|
| Anonymous API | GET `/api/tickets` | 401 | pytest + HTTP smoke |
| Employee changes ticket | PATCH `/api/tickets/{id}` | 403 | pytest + HTTP smoke |
| Self-approve request | request as employee, decide same role | 403 | pytest |
| Expired approval | alter expiry in isolated DB, decide | 410/closed | pytest |
| Forged Origin header | POST login from other origin | 403 | pytest |
| Password/OTP prompt injection | submit high-risk secret-containing chat | blocked/redacted | pytest |
| SOP prompt injection attempt | upload malicious instructions as SOP | 422 | pytest |
| Invalid source IDs | model proposes wrong citations | reject/retry/fallback | pytest (mock Ollama) |
| Unsupported question | outside available SOP knowledge | abstain / escalate | lexical + optional real live benchmark |
| Duplicate ticket | repeated idempotency key | one row | pytest + HTTP smoke + live 9-check test |
| Conflicting replay | key reused with different payload | reject | pytest |
| Signed webhook | valid HMAC vs invalid signature/timestamp | send accepted; spoof/replay rejected | independent `webhook_smoke.py` |
| SQL injection / arbitrary tool arguments | invalid tool schema | reject | pytest; not a complete pen test |
| Model unavailable | absent live service | no fabricated answer | local verifier BLOCKED + mock tests |
| Feedback double-submit | owner sends repeated outcome | 409 | v12 pytest |
| Feedback impersonation | another account posts on answer | 403 | v12 pytest |
| 60-request small load | concurrent localhost synthetic chat | no failed HTTP outcome | `load_smoke.py` |

## Known residual risks

- Demo login: no SSO/MFA or enterprise policy enforcement, session cookie HTTPS disabled in demo.
- Local SQLite: no externally verified backup/restore practice, encrypt-at-rest, HA or independent monitoring.
- Prompt injection: heuristic filters cannot prevent all attacks; backend action allowlists are the main protection.
- Local model quality: works on selected sample but no comprehensive model/red-team study.
- Uploadable SOPs are administrator-controlled but not independently approved by a real enterprise KB governance process.
- Public security audit, disaster recovery drill and penetration test are **not performed**.

## Explicit release decision

**Suitable for a supervised local academic defense. No-go for unattended public production deployment.** Do not change `AIHAS_ENV` to bypass startup safety checks.
