"""LangGraph workflow — wires all nodes into a StateGraph with conditional edges."""

from __future__ import annotations
from langgraph.graph import StateGraph, END, START
from app.models.state import GraphState

# Import all nodes
from app.graph.nodes.preprocessor import preprocessor_node
from app.graph.nodes.followup_detector import followup_detector_node
from app.graph.nodes.context_resolver import context_resolver_node
from app.graph.nodes.classifier import classifier_node
from app.graph.nodes.intake_analyzer import intake_analyzer_node
from app.graph.nodes.planner import planner_node
from app.graph.nodes.tool_executor import tool_executor_node
from app.graph.nodes.aggregator import aggregator_node
from app.graph.nodes.reasoner import reasoner_node
from app.graph.nodes.formatter import formatter_node
from app.graph.nodes.graph_extractor_node import graph_extractor_node


def _after_intake(state: GraphState) -> str:
    """
    Combined conditional edge after intake_analyzer.

    Three outcomes:
      - "end"      → pipeline terminates (clarification question was emitted)
      - "planner"  → proceed to tool research
      - "reasoner" → skip tools, go straight to reasoning
    """
    if state.get("needs_clarification", False):
        return "end"

    classification = state.get("classification", {})
    needs_statutes = classification.get("needs_statutes", False)
    needs_cases = classification.get("needs_cases", False)

    if needs_statutes or needs_cases:
        return "planner"
    else:
        return "reasoner"


def build_workflow() -> StateGraph:
    """Build and return the compiled LangGraph workflow."""

    graph = StateGraph(GraphState)

    # ── Add all nodes ──
    graph.add_node("preprocessor", preprocessor_node)
    graph.add_node("followup_detector", followup_detector_node)
    graph.add_node("context_resolver", context_resolver_node)
    graph.add_node("classifier", classifier_node)
    graph.add_node("intake_analyzer", intake_analyzer_node)
    graph.add_node("planner", planner_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("aggregator", aggregator_node)
    graph.add_node("reasoner", reasoner_node)
    graph.add_node("formatter", formatter_node)
    graph.add_node("graph_extractor", graph_extractor_node)

    # ── Define edges ──

    # Linear chain: START → preprocessor → followup_detector → context_resolver → classifier
    graph.add_edge(START, "preprocessor")
    graph.add_edge("preprocessor", "followup_detector")
    graph.add_edge("followup_detector", "context_resolver")
    graph.add_edge("context_resolver", "classifier")

    # Classifier → Intake Analyzer (always)
    graph.add_edge("classifier", "intake_analyzer")

    # Intake Analyzer → Conditional (3-way)
    graph.add_conditional_edges(
        "intake_analyzer",
        _after_intake,
        {
            "end": END,            # Clarification emitted — stop here
            "planner": "planner",  # Has enough info + needs tools
            "reasoner": "reasoner",  # Has enough info + skip tools
        },
    )

    # Tool pipeline: Planner → Tool Executor → Aggregator → Reasoner
    graph.add_edge("planner", "tool_executor")
    graph.add_edge("tool_executor", "aggregator")
    graph.add_edge("aggregator", "reasoner")

    # Reasoner → Formatter → Graph Extractor → END
    graph.add_edge("reasoner", "formatter")
    graph.add_edge("formatter", "graph_extractor")
    graph.add_edge("graph_extractor", END)

    return graph.compile()


# Singleton compiled graph
legal_graph = build_workflow()
