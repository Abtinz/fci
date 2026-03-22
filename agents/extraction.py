"""Data Extraction Agent - pulls raw data from discovered sources."""

from __future__ import annotations

import json
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from agents.llm import get_llm
from tools.crawler import fetch_source
from prompts.extraction import SYSTEM, TASK
from schema.graph import PipelineState

# ── Colors ───────────────────────────────────────────────────────────────────
G = "\033[32m"; R = "\033[31m"; M = "\033[35m"
DIM = "\033[2m"; BOLD = "\033[1m"; RESET = "\033[0m"


# ── Extraction-specific tools ───────────────────────────────────────────────

@tool
def format_extraction_result(
    raw_value: str,
    numeric_value: float | None = None,
    unit: str = "",
    context: str = "",
) -> str:
    """Format the final extraction result. Call this when you've found the data point.
    Args:
        raw_value: The exact text/number found in the source.
        numeric_value: The numeric value if applicable (e.g., 4.1).
        unit: The unit of measurement (e.g., '%', 'units', 'rides').
        context: Brief note on what was found and where.
    """
    return json.dumps({
        "raw_value": raw_value,
        "numeric_value": numeric_value,
        "unit": unit,
        "context": context,
    })


TOOLS = [fetch_source, format_extraction_result]


def create_extraction_agent():
    return create_react_agent(get_llm(), TOOLS, prompt=SYSTEM)


# ── Node function for orchestrator ──────────────────────────────────────────

def run_extraction(state: PipelineState) -> PipelineState:
    """LangGraph node: run the extraction agent."""
    init = state["initiative"]
    sources = state.get("sources", [])

    print(f"\n{R}{BOLD}[EXTRACTION]{RESET} {init['name']}")

    if not sources:
        print(f"  {R}no sources to extract from{RESET}")
        return {**state, "extracted": []}

    extracted = []
    for source in sources:
        url = source.get("url", "")
        source_type = source.get("source_type", "html")
        description = source.get("description", "")

        print(f"  {DIM}extracting from{RESET} {url[:80]}...")

        task = TASK.format(
            name=init["name"],
            metric_label=init["metric_label"],
            target_value=init["target_value"],
            source_url=url,
            source_type=source_type,
            source_description=description,
        )

        agent = create_extraction_agent()
        result = agent.invoke({"messages": [("user", task)]})

        # Parse the extraction result
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content:
                try:
                    parsed = json.loads(msg.content)
                    if isinstance(parsed, dict) and "raw_value" in parsed:
                        parsed["source_url"] = url
                        extracted.append(parsed)
                        val = parsed.get("raw_value", "")
                        num = parsed.get("numeric_value", "")
                        unit = parsed.get("unit", "")
                        ctx = parsed.get("context", "")
                        print(f"  {G}extracted:{RESET} {val} {num}{unit} {DIM}({ctx}){RESET}")
                        break
                except (json.JSONDecodeError, TypeError):
                    continue

    if not extracted:
        print(f"  {R}extraction failed{RESET}")

    return {**state, "extracted": extracted}
