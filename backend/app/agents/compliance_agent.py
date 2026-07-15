"""
Compliance review agent — answers KYC/AML and regulatory questions grounded in
retrieved policy and regulatory documents, with mandatory source citation
since compliance answers must be auditable.
"""
from langchain_openai import ChatOpenAI

from app.agents.common import build_sources, format_context
from app.agents.state import AgentState
from app.core.config import settings

_llm = ChatOpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.0)

SYSTEM_PROMPT = """You are a compliance review assistant for a financial institution.
Answer strictly from the provided context (regulatory documents, internal policy, KYC/AML
procedures). Every factual claim MUST be attributed to a numbered source. If the context
is insufficient to give a compliant answer, explicitly say the answer requires review by
a licensed compliance officer rather than guessing.

Context:
{context}

Question: {query}

Answer (with inline source citations like [Source 1]):"""


async def run_compliance_agent(state: AgentState) -> AgentState:
    prompt = SYSTEM_PROMPT.format(context=format_context(state), query=state["query"])
    response = await _llm.ainvoke(prompt)
    return {**state, "answer": response.content, "sources": build_sources(state)}
