"""
Fraud investigation agent.

Grounds its narrative explanation in retrieved policy/case documents, and is
designed to sit alongside (not replace) the quantitative XGBoost fraud model —
this agent explains *why* a transaction was flagged in natural language,
citing relevant fraud policy and historical case documents.
"""
from langchain_openai import ChatOpenAI

from app.agents.common import build_sources, format_context
from app.agents.state import AgentState
from app.core.config import settings

_llm = ChatOpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.2)

SYSTEM_PROMPT = """You are a fraud investigation analyst assistant for a financial institution.
Use ONLY the provided context to explain potential fraud indicators, cite fraud policy,
or summarize a case. Be precise, cite sources by number (e.g. "Source 2"), and never
invent transaction details that are not present in the context. If the context does not
answer the question, say so explicitly and recommend escalation to a human fraud analyst.

Context:
{context}

Question: {query}

Answer:"""


async def run_fraud_agent(state: AgentState) -> AgentState:
    prompt = SYSTEM_PROMPT.format(context=format_context(state), query=state["query"])
    response = await _llm.ainvoke(prompt)
    return {**state, "answer": response.content, "sources": build_sources(state)}
