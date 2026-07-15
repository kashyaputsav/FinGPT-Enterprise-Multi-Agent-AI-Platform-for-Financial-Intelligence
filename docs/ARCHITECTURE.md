# Architecture

## Request flow

1. **ALB** terminates TLS and forwards to the ECS Fargate service (2+ tasks,
   CPU-target autoscaled 2–6).
2. **FastAPI** (`app/main.py`) authenticates the request (JWT bearer token),
   validates the payload against a Pydantic schema, and routes to a versioned
   endpoint under `/api/v1`.
3. For `/agents/query`, the request enters the **LangGraph orchestrator**
   (`app/agents/graph.py`):
   - `route` — an LLM classification node picks one of `fraud`,
     `underwriting`, `compliance`, `assistant` (or accepts a forced choice
     from the client).
   - `retrieve` — a shared hybrid-RAG node (`app/rag/retriever.py`) embeds the
     query, runs dense retrieval against **Qdrant**, and reranks candidates
     with a cross-encoder for precision.
   - The chosen specialist node generates a grounded, cited answer using only
     the retrieved context — this is what keeps compliance/fraud answers
     auditable rather than hallucinated.
4. Every agent invocation is persisted to **`agent_runs`** in Postgres
   (query, answer, sources, latency) for audit and analytics.

## RAG pipeline details

- **Ingestion** (`app/rag/ingestion.py`): documents are split with a
  sentence-aware splitter (512 tokens, 64 overlap) to avoid breaking financial
  clauses mid-sentence, embedded with `text-embedding-3-large`, and upserted
  into a Qdrant collection with both dense and (optionally) sparse vectors.
- **Retrieval**: dense cosine search returns ~20 candidates; a cross-encoder
  (`cross-encoder/ms-marco-MiniLM-L-6-v2`) reranks down to the top 5 by actual
  query-passage relevance, which measurably improves precision over
  vector-similarity alone.
- **Source citation**: every chunk returned to an agent carries its
  `document_id`, `filename`, and `chunk_index`, which flow straight through to
  the API response as `SourceCitation` objects — the frontend can deep-link
  back to the exact passage.

## Fraud & underwriting: quantitative + generative split

The platform deliberately separates two concerns that are easy to conflate:

- **Quantitative scoring** (`app/services/fraud_service.py`,
  `underwriting_service.py`) — a trained XGBoost classifier (SMOTE-balanced,
  SHAP-explained; 93% precision / 85% recall on the reference fraud model)
  produces the actual risk score / approve-reject decision. This is
  deterministic, auditable, and doesn't hallucinate.
- **Generative explanation** (`fraud_agent.py`, `underwriting_agent.py`) — the
  LLM agent explains *why*, in natural language, grounded in retrieved policy
  documents, but is explicitly instructed never to invent a final decision
  itself for underwriting.

This mirrors how real fintech risk teams operate: a model scores, a human (or
a cited, auditable assistant) explains.

## Data model

```
users (id, email, hashed_password, role, is_active)
documents (id, owner_id, filename, doc_type, s3_key, status)
document_chunks (id, document_id, chunk_index, content, qdrant_point_id)
agent_runs (id, user_id, agent_name, input_query, output_response, sources, latency_ms)
audit_logs (id, user_id, action, resource, details)
```

`document_chunks.qdrant_point_id` links a Postgres row to its vector in
Qdrant, so metadata (ownership, access control) lives in Postgres while
embeddings live in Qdrant — deleting a document cascades to both.

## Security

- JWT access (30 min) + refresh (7 day) tokens, bcrypt password hashing.
- Role-gated endpoints via `require_role(...)` dependency (e.g. compliance
  officer-only routes can be added trivially).
- ECS tasks run in **private subnets** with no public IP; only the ALB is
  internet-facing. Security groups allow only ALB→ECS, ECS→RDS, ECS→Redis,
  ECS→Qdrant — nothing else.
- Secrets (JWT signing key, DB password, OpenAI key) are stored in **AWS
  Secrets Manager** and injected as container secrets, never baked into the
  image or committed to the repo.

## Observability

- Structured JSON logs (`structlog`) — queryable via CloudWatch Logs
  Insights.
- `/metrics` (Prometheus format) exposed via
  `prometheus-fastapi-instrumentator` for scraping into CloudWatch Container
  Insights or a self-hosted Prometheus/Grafana stack.
- ALB target group health checks hit `/api/v1/health`; ECS replaces unhealthy
  tasks automatically.
