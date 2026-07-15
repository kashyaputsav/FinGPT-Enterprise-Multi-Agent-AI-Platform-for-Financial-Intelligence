"""
Loan underwriting agent — explains and supports credit decisions by grounding
its reasoning in the applicant's documents (statements, KYC) and lending policy
retrieved via RAG. Final numeric decisions should still be produced by a
dedicated scoring model (see app/services/underwriting_service.py); this agent
handles the natural-language explanation and policy-lookup layer.
"""
from langchain_openai import ChatOpenAI

from app.agents.common import build_sources, format_context
from app.agents.state import AgentState
from app.core.config import settings

_llm = ChatOpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.1)

SYSTEM_PROMPT = """You are a loan underwriting assistant. Use ONLY the provided context
(lending policy documents, applicant statements/KYC excerpts) to answer the question.
Explain relevant underwriting criteria, cite sources by number, and flag any missing
information that a human underwriter would need before making a final decision.
Never state a final approve/reject decision yourself — defer that to the underwriting
decision engine — but you may explain how the criteria in the context would apply.

Context:
{context}

Question: {query}

Answer:"""


async def run_underwriting_agent(state: AgentState) -> AgentState:
    prompt = SYSTEM_PROMPT.format(context=format_context(state), query=state["query"])
    response = await _llm.ainvoke(prompt)
    return {**state, "answer": response.content, "sources": build_sources(state)}
