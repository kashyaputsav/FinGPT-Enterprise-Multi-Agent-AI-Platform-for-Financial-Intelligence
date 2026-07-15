"""Pydantic request/response schemas (API contracts, distinct from ORM models)."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# --- Documents ---
class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    doc_type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Agent / chat ---
AgentName = Literal["fraud", "underwriting", "compliance", "assistant"]


class AgentQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    agent: AgentName | None = Field(
        default=None, description="Force a specific agent; omit to let the orchestrator route it."
    )
    document_ids: list[uuid.UUID] | None = Field(
        default=None, description="Restrict retrieval to these documents"
    )
    conversation_id: uuid.UUID | None = None


class SourceCitation(BaseModel):
    document_id: uuid.UUID
    filename: str
    chunk_index: int
    excerpt: str
    score: float


class AgentQueryResponse(BaseModel):
    agent_used: AgentName
    answer: str
    sources: list[SourceCitation]
    latency_ms: float


# --- Fraud ---
class FraudCheckRequest(BaseModel):
    transaction_id: str
    amount: float
    merchant: str
    location: str | None = None
    device_fingerprint: str | None = None


class FraudCheckResponse(BaseModel):
    transaction_id: str
    risk_score: float
    is_flagged: bool
    reasons: list[str]
    shap_top_features: list[dict]


# --- Underwriting ---
class LoanApplicationRequest(BaseModel):
    applicant_name: str
    annual_income: float
    credit_score: int = Field(ge=300, le=900)
    loan_amount: float
    loan_purpose: str
    existing_debt: float = 0.0


class LoanDecisionResponse(BaseModel):
    decision: Literal["approved", "rejected", "manual_review"]
    confidence: float
    rationale: str
    conditions: list[str] = []
