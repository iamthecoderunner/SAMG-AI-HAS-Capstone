# AI-HAS v12 — Database relationships and API specification

## Operational database vs vector database

- **SQLite (`aihas.db`)**: transactional accounts, tickets, conversations, feedback, approvals, audit and delivery events; local academic prototype persistence.
- **ChromaDB (`chroma` path)**: embeddings/chunks for semantic SOP retrieval; generated from currently stored SOP documents, not the authority for ticket records.
- **Ollama (`localhost:11434`)**: model inference and embeddings, not a durable source of ticket state.

## ERD (simplified)

```mermaid
erDiagram
  USERS ||--o{ CONVERSATIONS : asks
  USERS ||--o{ TICKETS : creates
  USERS ||--o{ APPROVALS : requests
  USERS ||--o{ CONVERSATION_FEEDBACK : reports
  CONVERSATIONS ||--o| CONVERSATION_FEEDBACK : rated_once
  TICKETS ||--o{ TICKET_EVENTS : changes
  TICKETS ||--o{ TICKET_REQUESTS : deduplicated_by
  TICKETS ||--o{ WEBHOOK_EVENTS : triggers
  USERS { int id PK string username string role string password_hash }
  DOCUMENTS { int id PK string title string body int version }
  CONVERSATIONS { int id PK int user_id FK string question string response string outcome int latency_ms }
  CONVERSATION_FEEDBACK { int id PK int conversation_id FK int user_id FK bool resolved }
  TICKETS { int id PK int user_id FK string category string description string status }
  TICKET_EVENTS { int id PK int ticket_id FK string previous_status string new_status }
  TICKET_REQUESTS { int id PK int user_id FK string request_key string payload_hash int ticket_id FK }
  APPROVALS { int id PK int user_id FK string request_type string details string status string request_digest }
  WEBHOOK_EVENTS { int id PK string event_type int resource_id string status int attempts }
  AUDIT { int id PK string actor string action string details }
```

## Main API routes (full machine-readable spec in `API_OpenAPI_v12.json`)

| Verb | Route | Role | Purpose |
|---|---|---|---|
| POST | `/api/login` | anonymous | Session login, throttled |
| POST | `/api/chat` | authenticated | RAG or model-proposed ticket creation; returns `conversation_id`, mode, citations, outcome |
| POST | `/api/conversations/{id}/feedback` | owner only | One Yes/No resolution outcome for answered chat |
| POST | `/api/tickets` | authenticated | Ticket create; optional Idempotency-Key |
| GET | `/api/tickets` | authenticated | Owner-visible or staff queue |
| PATCH | `/api/tickets/{id}` | staff | Controlled state transition |
| GET | `/api/tickets/{id}/history` | owner/staff | Ticket timeline |
| POST | `/api/escalations` | authenticated | Human helpdesk escalation |
| POST | `/api/approvals` | authenticated | Simulated privileged action request |
| POST | `/api/approvals/{id}/decision` | staff | Simulated approval/denial only |
| GET/POST/PUT/DELETE | `/api/documents*` | read=authenticated; mutate=admin | SOP listing, ingestion, revisions |
| GET | `/api/metrics` | staff | Operational counts and self-reported feedback |
| GET | `/api/audit` | admin | Audit trail |
| GET/POST | `/api/outbox*` | admin | Delivery records, bounded retry |
| GET | `/api/health` | public localhost | Health/status (not provider health certification) |

## Data integrity

- DB commits are transactional; explicit rollback on exceptions; foreign keys enabled.
- Ticket replay key uniqueness and payload digest prevent repeated created tickets.
- SOP optimistic version check prevents stale updates overwriting newer content.
- One feedback record per conversation enforced by unique relationship.
- Request approval compares a digest and expiry, but is NOT a cryptographically signed approval token.
- Staff actions and tool outcomes are audited; minimum-information event payloads delivered by webhook.

## Limitations

SQLite is appropriate for a small demonstration but is not a production HA database. There is no enterprise-managed IAM, row-level multitenant isolation, at-rest encryption guarantee, or production secrets vault.
