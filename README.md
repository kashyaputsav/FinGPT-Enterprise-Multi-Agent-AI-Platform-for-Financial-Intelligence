# FinGPT Enterprise

Production-grade multi-agent Generative AI platform for financial intelligence — fraud
investigation, loan underwriting, compliance review, document analysis, and a
personalized financial assistant, built on LangGraph, FastAPI, and a hybrid RAG
pipeline over Qdrant + PostgreSQL.

## Architecture

```
                        ┌─────────────────────┐
                        │   ALB (HTTPS/443)   │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  ECS Fargate Service │
                        │   (FastAPI app x N)  │
                        └──────────┬──────────┘
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
        ┌────────▼───────┐ ┌───────▼──────┐  ┌───────▼───────┐
        │  RDS Postgres   │ │  Qdrant Cloud │  │  S3 (docs +   │
        │  (metadata,     │ │  or ECS       │  │  embeddings   │
        │   auth, audit)  │ │  self-hosted  │  │   cache)      │
        └─────────────────┘ └──────────────┘  └───────────────┘
                 │
        ┌────────▼───────┐
        │  ElastiCache    │
        │  Redis (cache,  │
        │  rate limiting) │
        └─────────────────┘
```

The orchestrator agent (LangGraph) routes each request to one of four specialist
agents — **Fraud Investigation**, **Loan Underwriting**, **Compliance Review**, or
**Financial Assistant** — each of which pulls grounded context from the RAG layer
(hybrid dense + sparse retrieval, cross-encoder reranking, inline source citation)
before generating a response.

## Repository layout

```
fingpt-enterprise/
├── backend/                  # FastAPI application (see backend/README.md)
│   ├── app/
│   │   ├── core/              # config, security, logging, exceptions
│   │   ├── api/v1/            # versioned REST routers
│   │   ├── agents/            # LangGraph agent graph + nodes
│   │   ├── rag/                # ingestion, embeddings, retriever, reranker
│   │   ├── models/             # Pydantic schemas + SQLAlchemy models
│   │   ├── db/                 # session, base, init
│   │   ├── services/           # business logic layer
│   │   └── utils/
│   ├── tests/
│   ├── alembic/                # DB migrations
│   ├── Dockerfile
│   └── requirements.txt
├── infra/
│   ├── docker-compose.yml      # local dev stack (api, postgres, qdrant, redis)
│   └── aws/
│       ├── terraform/          # VPC, ECS, RDS, ALB, ECR, IAM, Secrets Manager
│       └── ecs/                # ECS task definition + deploy scripts
├── .github/workflows/          # CI/CD (test → build → push ECR → deploy ECS)
├── docs/
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
└── scripts/                    # helper scripts (seed data, local bootstrap)
```

## Quick start (local)

```bash
cp .env.example .env                 # fill in secrets
docker compose -f infra/docker-compose.yml up --build
# API docs at http://localhost:8000/docs
```

## Deploying to AWS

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the full walkthrough
(Terraform apply → ECR push → ECS service update). Summary:

```bash
cd infra/aws/terraform
terraform init
terraform apply -var-file=prod.tfvars

# CI/CD (GitHub Actions) builds the image, pushes to ECR, and triggers
# an ECS rolling deployment on every push to `main`.
```

## Tech stack

| Layer            | Technology |
|------------------|------------|
| API              | FastAPI, Uvicorn/Gunicorn |
| Agent Orchestration | LangGraph, LangChain |
| RAG              | Qdrant (hybrid search), LlamaIndex, sentence-transformers reranker |
| Data             | PostgreSQL (RDS), Redis (ElastiCache), S3 |
| Auth             | JWT (OAuth2 password + refresh flow) |
| Infra            | Docker, ECS Fargate, ALB, Terraform |
| CI/CD            | GitHub Actions → ECR → ECS |
| Observability    | Structured JSON logging, CloudWatch, Prometheus-compatible `/metrics` |
