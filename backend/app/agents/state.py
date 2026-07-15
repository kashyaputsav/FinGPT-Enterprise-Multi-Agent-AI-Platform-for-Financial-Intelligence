"""Shared state object passed between nodes in the LangGraph orchestration graph."""
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    query: str
    document_ids: list[str] | None
    route: str  # fraud | underwriting | compliance | assistant
    context_chunks: list[dict[str, Any]]
    answer: str
    sources: list[dict[str, Any]]
    error: str | None
