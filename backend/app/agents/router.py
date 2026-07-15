"""
Orchestrator routing node: classifies an incoming query into one of the four
specialist agents using a lightweight LLM classification call.
"""
from langchain_openai import ChatOpenAI

from app.agents.state import AgentState
from app.core.config import settings

_router_llm = ChatOpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0)

ROUTER_PROMPT = """You are a routing classifier for a financial services AI platform.
Classify the user's query into exactly one category:

- fraud: suspicious transactions, chargebacks, fraud investigation, anomaly review
- underwriting: loan applications, credit decisions, affordability, risk scoring for lending
- compliance: KYC/AML, regulatory obligations, policy questions, audit/reporting requirements
- assistant: general financial questions, account questions, anything not clearly the above

Respond with only the single category word, nothing else.

Query: {query}
Category:"""


async def route_query(state: AgentState) -> AgentState:
    if state.get("route"):
        # Caller explicitly forced an agent — skip classification.
        return state

    prompt = ROUTER_PROMPT.format(query=state["query"])
    response = await _router_llm.ainvoke(prompt)
    label = response.content.strip().lower()

    if label not in {"fraud", "underwriting", "compliance", "assistant"}:
        label = "assistant"

    return {**state, "route": label}


def route_decision(state: AgentState) -> str:
    """Conditional-edge function used by the LangGraph graph builder."""
    return state.get("route", "assistant")
