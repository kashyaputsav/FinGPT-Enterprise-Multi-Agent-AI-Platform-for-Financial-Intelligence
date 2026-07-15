"""Service layer wrapping graph invocation, timing, and audit persistence."""
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import get_graph
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.models.audit import AgentRun

logger = get_logger(__name__)


async def run_agent_query(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    forced_agent: str | None,
    document_ids: list[uuid.UUID] | None,
) -> dict:
    graph = get_graph()
    start = time.perf_counter()

    initial_state = {
        "query": query,
        "document_ids": [str(d) for d in document_ids] if document_ids else None,
        "route": forced_agent,
    }

    try:
        result = await graph.ainvoke(initial_state)
    except Exception as exc:  # noqa: BLE001
        logger.error("agent_graph_failed", error=str(exc), user_id=str(user_id))
        raise AgentExecutionError(f"Agent execution failed: {exc}") from exc

    latency_ms = (time.perf_counter() - start) * 1000

    run = AgentRun(
        user_id=user_id,
        agent_name=result.get("route", "assistant"),
        input_query=query,
        output_response=result.get("answer", ""),
        sources=result.get("sources", []),
        latency_ms=latency_ms,
    )
    db.add(run)
    await db.commit()

    return {
        "agent_used": result.get("route", "assistant"),
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "latency_ms": latency_ms,
    }
