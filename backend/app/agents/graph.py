"""
Builds the LangGraph orchestration graph:

    START -> route -> retrieve -> {fraud|underwriting|compliance|assistant} -> END

The router node classifies (or accepts a forced) agent choice, a shared retrieval
node fetches grounded RAG context, and exactly one specialist node generates the
final cited answer.
"""
from langgraph.graph import END, START, StateGraph

from app.agents.assistant_agent import run_assistant_agent
from app.agents.compliance_agent import run_compliance_agent
from app.agents.fraud_agent import run_fraud_agent
from app.agents.retrieval_node import retrieve_context
from app.agents.router import route_decision, route_query
from app.agents.state import AgentState
from app.agents.underwriting_agent import run_underwriting_agent

_compiled_graph = None


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("route", route_query)
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("fraud", run_fraud_agent)
    graph.add_node("underwriting", run_underwriting_agent)
    graph.add_node("compliance", run_compliance_agent)
    graph.add_node("assistant", run_assistant_agent)

    graph.add_edge(START, "route")
    graph.add_edge("route", "retrieve")

    graph.add_conditional_edges(
        "retrieve",
        route_decision,
        {
            "fraud": "fraud",
            "underwriting": "underwriting",
            "compliance": "compliance",
            "assistant": "assistant",
        },
    )

    graph.add_edge("fraud", END)
    graph.add_edge("underwriting", END)
    graph.add_edge("compliance", END)
    graph.add_edge("assistant", END)

    return graph.compile()


def get_graph():
    """Lazily compile and cache the graph (compilation is not free — do it once)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
