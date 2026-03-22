"""Reporter Agent - generates human-readable summaries and alerts."""

from __future__ import annotations

from agents.llm import get_llm
from prompts.reporter import SYSTEM, TASK
from schema.graph import PipelineState

# ── Colors ───────────────────────────────────────────────────────────────────
C = "\033[36m"; DIM = "\033[2m"; BOLD = "\033[1m"; RESET = "\033[0m"


def run_reporter(state: PipelineState) -> PipelineState:
    """LangGraph node: generate a summary report for one initiative."""
    init = state["initiative"]
    extracted = state.get("extracted", [])

    print(f"\n{C}{BOLD}[REPORTER]{RESET} {init['name']}")

    source_url = ""
    raw_value = ""
    unit = ""
    if extracted:
        source_url = extracted[0].get("source_url", "")
        raw_value = extracted[0].get("raw_value", "")
        unit = extracted[0].get("unit", "")

    task = TASK.format(
        name=init["name"],
        id=init["id"],
        category=init["category"],
        source_url=source_url,
        raw_value=raw_value,
        unit=unit,
        status=state.get("status", "NO_ASSESSMENT"),
        status_reasoning=state.get("status_reasoning", ""),
        errors=state.get("validation_errors", []),
    )

    llm = get_llm()
    response = llm.invoke([
        ("system", SYSTEM),
        ("user", task),
    ])

    print(f"  {DIM}{response.content[:120]}...{RESET}")

    return state


def run_exhausted(state: PipelineState) -> PipelineState:
    """Terminal node for exhausted retries."""
    init = state["initiative"]
    errors = state.get("validation_errors", [])
    print(f"\n\033[31m{BOLD}[EXHAUSTED]{RESET} {init['name']} -> NO_ASSESSMENT after max retries")
    print(f"  {DIM}errors: {errors}{RESET}")

    return {
        **state,
        "status": "NO_ASSESSMENT",
        "status_reasoning": f"Exhausted retries. Errors: {errors}",
    }
