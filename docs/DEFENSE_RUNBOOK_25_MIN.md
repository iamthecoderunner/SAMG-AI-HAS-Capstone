# AI-HAS — Presenter runbook: 20-minute presentation + 5-minute Q&A

**Fill in actual member names before presentation.** Timing is a rehearsable target, not an automatic guarantee. All demo accounts and SOPs are synthetic.

| Clock | Slides | Speaking responsibility | Specific demonstration or claim |
|---|---|---|---|
| **00:00–02:00** | 1–2 | Team lead + roles | Introduce problem, team member names/roles; distinguish live demo from simulated admin actions |
| **02:00–06:00** | 3–5 | Lead | Ticket load, grounding challenges, objectives, MVP workflows + acceptance criteria |
| **06:00–10:00** | 6–8 | AI/RAG + backend | Diagram, data/trust boundaries, cited Ollama + Chroma workflow, validated ticket function, approval gate |
| **10:00–15:00** | 9–12 | Demonstrator | 1) Live VPN `semantic+ollama` with `[1]`; 2) actual ticket tool call and new ID; 3) agent queue/status; 4) simulated access approval; 5) dashboard/RBAC/audit. Keep a screenshot backup. |
| **15:00–18:00** | 13–15 | QA | Proven tests vs unmeasured goals, security/failure demonstrations, sample latency (not average) |
| **18:00–20:00** | 16–17 | Lead | Conclusions, limitations and scoped future work |
| **20:00–25:00** | 18–20 | All | Panel Q&A and appendix evidence |

## Demo checklist (prepare BEFORE the timer starts)

- Ollama running with `qwen3:4b` and `nomic-embed-text` available; Chroma dependency installed.
- Working `.env` preserved privately; `AI_PROVIDER=ollama`, `RAG_MODE=semantic`, `REQUIRE_SEMANTIC_RAG=1`, `ENABLE_TOOL_CALLING=1`.
- Local server at `http://127.0.0.1:8000`, demo employee / agent / admin passwords stored privately (not on slides).
- Open employee session and agent/admin session in separate browser profiles to avoid logging out while switching roles.
- Run `CHECK_FREE_AI_WINDOWS.bat` immediately before presenting; keep PASS JSON and screenshot. Run the new live 6-case RAG benchmark if time permits; present results even if failures are observed.
- One prepared new ticket request description: `My company VPN disconnects after sign-in; please create a helpdesk ticket for investigation.`
- One approval scenario: `Request access to design software to prepare department reports.` Explicitly label approval as simulation.
- No production passwords, student personal identifiers, or real employee information entered.

## Exact live demonstration within five minutes

**10:00–11:20:** Employee login; ask `How can I troubleshoot VPN issues?` Show correct SOP citation, mode `semantic+ollama`, and user feedback Yes/No; describe model generation vs deterministic fallback.

**11:20–12:20:** Ask the model to create the prepared VPN ticket. Show `ollama_function_call`, `tool_ticket_created`, and ID; explain that the model requested the tool but backend performed validated persistence. If it fails, use ticket form and disclose model tool failure.

**12:20–13:20:** Open agent queue; show same ID; change status from open to in progress; refresh to prove persistence; show ticket history.

**13:20–14:05:** Create software access approval; approve as agent, showing `simulated_only`. Mention lack of real provisioning by design.

**14:05–15:00:** Show admin KPI dashboard, resolution-feedback count, audit/outbox and attempt one employee-restricted endpoint. Do not claim self-reported feedback equals ticket deflection.

## If Ollama fails mid-presentation

1. State the model is unavailable; do not claim an observed output that did not happen.
2. Show the actual prior verifier PASS JSON and the saved real screenshot with time/source.
3. Show deterministic SOP fallback **explicitly labeled fallback**, plus ticket/API persistence and agent queue.
4. Demonstrate the safety gate: no uncited fabricated answer or unauthorized action.
5. Note the failure as an operational limitation, not a hidden success.

## Panel questions — concise accurate answers

**Is this really an LLM?** Yes, live student-machine tests confirmed Qwen3 generation and model-requested ticket function calling. The database and authorization remain deterministic.

**Why semantic RAG?** Company-specific SOP context, retrieved by embeddings and ChromaDB, limits unsupported generic advice and allows cited source checks.

**Are citations always true?** No. Backend validates IDs and prevents unrelated citations; human faithfulness review is still needed for factual completeness.

**Where is the multi-agent architecture?** Not claimed. This rubric asks for helpdesk RAG and automation; this is a single bounded assistant with backend orchestration.

**Does approval reset real passwords?** No. It is clearly simulated and access-controlled; real identity workflows require secure integration and verification.

**Are you reducing MTTR?** That's a project objective, not a measured outcome here. We record ticket timestamps and response latencies, but no controlled enterprise baseline exists.

**Why no OpenAI API?** A local Ollama model provides genuine LLM inference and tool calling without paid API usage; the official specification recommends technologies rather than mandating paid OpenAI access.

**Is the system production-ready?** No. The demo mode deliberately blocks a public production setting. Enterprise identity, operational resilience, pen testing and a compliant deployment would be future work.

**What happens on model failure?** One bounded retry; verified SOP extract only when strongly supported; otherwise abstain and escalate. No invented success.

**What did RCTC change?** It constrained the assistant role, approved context, exact permitted tasks and negative controls; validation also exists in Python, not just a prompt.
