"""Shared helpers used across specialist agent nodes."""
from app.agents.state import AgentState


def format_context(state: AgentState) -> str:
    chunks = state.get("context_chunks", [])
    if not chunks:
        return "No relevant context was found in the knowledge base."

    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(f"[Source {i}: {c['filename']} | chunk {c['chunk_index']}]\n{c['content']}")
    return "\n\n".join(blocks)


def build_sources(state: AgentState) -> list[dict]:
    sources = []
    for c in state.get("context_chunks", []):
        sources.append(
            {
                "document_id": c.get("document_id"),
                "filename": c.get("filename"),
                "chunk_index": c.get("chunk_index"),
                "excerpt": c["content"][:280],
                "score": c.get("rerank_score", 0.0),
            }
        )
    return sources
