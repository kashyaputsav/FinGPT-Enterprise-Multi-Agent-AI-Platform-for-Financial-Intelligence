"""General-purpose personalized financial assistant agent (fallback route)."""
from langchain_openai import ChatOpenAI

from app.agents.common import build_sources, format_context
from app.agents.state import AgentState
from app.core.config import settings

_llm = ChatOpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.4)

SYSTEM_PROMPT = """You are a helpful financial assistant. Use the provided context where
relevant, and be transparent when you're answering from general knowledge instead of the
retrieved documents. Keep answers concise and actionable.

Context:
{context}

Question: {query}

Answer:"""


async def run_assistant_agent(state: AgentState) -> AgentState:
    prompt = SYSTEM_PROMPT.format(context=format_context(state), query=state["query"])
    response = await _llm.ainvoke(prompt)
    return {**state, "answer": response.content, "sources": build_sources(state)}
