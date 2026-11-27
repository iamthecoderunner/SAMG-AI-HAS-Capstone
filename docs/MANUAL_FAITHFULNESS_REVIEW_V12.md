# Manual review worksheet for actual Ollama answers

Do this **after** `RUN_LIVE_RAG_EVALUATION_WINDOWS.bat` or `python scripts/evaluate_local_rag.py --full`. Read the actual answer and cited SOP text side by side, never just the model-generated citation number. Get two reviewers where possible, and resolve disagreements explicitly.

**Ratings:** `SUPPORTED` = every substantive factual troubleshooting step is supported by a cited SOP; `UNSUPPORTED` = at least one new unsupported claim; `PARTIAL` = some necessary SOP steps missing or ambiguous; `N/A` = abstention or model failure. Do not invent ratings without reading actual responses.

| Case | Question/topic | Reviewer A | Reviewer B | Final decision | Comment / cited SOP |
|---|---|---|---|---|---|
| F-01 | VPN client fails to connect | TO REVIEW | TO REVIEW | TO REVIEW | |
| F-02 | VPN problem after restarting | TO REVIEW | TO REVIEW | TO REVIEW | |
| F-03 | Password reset assistance | TO REVIEW | TO REVIEW | TO REVIEW | |
| F-04 | Does bot actually reset passwords? | TO REVIEW | TO REVIEW | TO REVIEW | |
| F-05 | Software access business justification | TO REVIEW | TO REVIEW | TO REVIEW | |
| F-06 | Company email not synchronizing | TO REVIEW | TO REVIEW | TO REVIEW | |
| F-07 | MFA device time / lockout | TO REVIEW | TO REVIEW | TO REVIEW | |
| F-08 | How unresolved tickets escalate | TO REVIEW | TO REVIEW | TO REVIEW | |
| F-09 | Unsupported spacecraft question | TO REVIEW | TO REVIEW | TO REVIEW | |
| F-10 | Unsupported cryptocurrency forecast | TO REVIEW | TO REVIEW | TO REVIEW | |

**Calculate separately:** supported / reviewed factual answers, partial / reviewed, unsupported / reviewed, and correct abstention / unsupported cases. Include sample size and environment. Do not generalize ten synthetic questions to an enterprise production rate.
