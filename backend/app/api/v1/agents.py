from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.schemas import AgentQueryRequest, AgentQueryResponse
from app.models.user import User
from app.services.agent_service import run_agent_query

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(
    payload: AgentQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Routes the query through the LangGraph orchestrator to the appropriate
    specialist agent (fraud / underwriting / compliance / assistant), grounded
    in RAG context, and returns a cited answer.
    """
    result = await run_agent_query(
        db=db,
        user_id=current_user.id,
        query=payload.query,
        forced_agent=payload.agent,
        document_ids=payload.document_ids,
    )
    return result
