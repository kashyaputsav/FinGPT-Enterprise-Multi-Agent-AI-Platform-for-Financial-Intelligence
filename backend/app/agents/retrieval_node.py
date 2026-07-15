"""Shared RAG retrieval node — runs before any specialist agent generates its answer."""
from app.agents.state import AgentState
from app.rag.retriever import retrieve


async def retrieve_context(state: AgentState) -> AgentState:
    doc_ids = state.get("document_ids")
    chunks = await retrieve(query=state["query"], document_ids=doc_ids)
    return {**state, "context_chunks": chunks}
