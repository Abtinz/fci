"""Format Mapper Agent - assesses status against targets."""

from __future__ import annotations

import json
from langgraph.prebuilt import create_react_agent

from agents.llm import get_llm
from tools.parser import compare_to_target, format_scorecard_entry
from prompts.mapper import SYSTEM, TASK
from schema.graph import PipelineState

# ── Colors ───────────────────────────────────────────────────────────────────
G = "\033[32m"; R = "\033[31m"; Y = "\033[33m"; B = "\033[34m"; M = "\033[35m"
DIM = "\033[2m"; BOLD = "\033[1m"; RESET = "\033[0m"

STATUS_COLORS = {
    "ACHIEVED": G, "ON_TRACK": G, "IN_PROGRESS": Y,
    "NEEDS_ATTENTION": R, "NO_ASSESSMENT": DIM,
}

TOOLS = [compare_to_target, format_scorecard_entry]


def create_mapper_agent():
    return create_react_agent(get_llm(), TOOLS, prompt=SYSTEM)


def run_mapper(state: PipelineState) -> PipelineState:
    """LangGraph node: run the mapper agent to assess status."""
    init = state["initiative"]
    extracted = state.get("extracted", [])

    print(f"\n{B}{BOLD}[MAPPER]{RESET} {init['name']}")

    if not extracted:
        print(f"  {DIM}no data -> NO_ASSESSMENT{RESET}")
        return {**state, "status": "NO_ASSESSMENT", "status_reasoning": "No data available"}

    extracted_summary = json.dumps(extracted, indent=2, default=str)
    task = TASK.format(**init, extracted_summary=extracted_summary)

    print(f"  {M}assessing status against target...{RESET}")
    agent = create_mapper_agent()
    result = agent.invoke({"messages": [("user", task)]})

    # Parse result
    status = "NO_ASSESSMENT"
    reasoning = ""

    for msg in reversed(result["messages"]):
        if hasattr(msg, "content") and msg.content:
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, dict) and "status" in parsed:
                    status = parsed["status"]
                    reasoning = parsed.get("reasoning", "")
                    break
            except (json.JSONDecodeError, TypeError):
                continue

    sc = STATUS_COLORS.get(status, "")
    print(f"  {sc}{BOLD}{status}{RESET} {DIM}{reasoning[:100]}{RESET}")

    return {**state, "status": status, "status_reasoning": reasoning}
