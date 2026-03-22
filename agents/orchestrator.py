"""LangGraph orchestrator - wires all agents into a pipeline."""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from schema.graph import PipelineState
from agents.discovery import run_discovery
from agents.extraction import run_extraction
from agents.validation import run_validation, should_retry
from agents.mapper import run_mapper
from agents.reporter import run_reporter, run_exhausted


def build_graph():
    """Build and compile the LangGraph pipeline."""
    graph = StateGraph(PipelineState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    graph.add_node("discovery", run_discovery)
    graph.add_node("extraction", run_extraction)
    graph.add_node("validation", run_validation)
    graph.add_node("mapper", run_mapper)
    graph.add_node("reporter", run_reporter)
    graph.add_node("exhausted", run_exhausted)

    # ── Edges ────────────────────────────────────────────────────────────────
    graph.set_entry_point("discovery")
    graph.add_edge("discovery", "extraction")
    graph.add_edge("extraction", "validation")

    # Conditional: validation -> mapper | retry | exhausted
    graph.add_conditional_edges(
        "validation",
        should_retry,
        {
            "mapper": "mapper",
            "retry": "discovery",
            "exhausted": "exhausted",
        },
    )

    graph.add_edge("mapper", "reporter")
    graph.add_edge("reporter", END)
    graph.add_edge("exhausted", END)

    return graph.compile()
