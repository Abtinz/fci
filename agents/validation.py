"""Validation Agent - deterministic data quality checks."""

from __future__ import annotations

from schema.graph import PipelineState

MAX_RETRIES = 3

# ── Colors ───────────────────────────────────────────────────────────────────
G = "\033[32m"; R = "\033[31m"; Y = "\033[33m"
DIM = "\033[2m"; BOLD = "\033[1m"; RESET = "\033[0m"


def run_validation(state: PipelineState) -> PipelineState:
    """LangGraph node: validate extracted data. Pure Python, no LLM."""
    init = state["initiative"]
    extracted = state.get("extracted", [])
    errors: list[str] = []

    print(f"\n{Y}{BOLD}[VALIDATION]{RESET} {init['name']}")

    # Check: any data at all?
    if not extracted:
        errors.append("No data extracted")
        print(f"  {R}FAIL: no data extracted{RESET}")

    # Check each extraction
    for item in extracted:
        raw = item.get("raw_value", "")

        if not raw:
            errors.append("Empty raw_value")
            print(f"  {R}FAIL: empty value{RESET}")

        if raw.startswith("Error:") or raw.startswith("HTTP error:"):
            errors.append(f"Extraction error: {raw}")
            print(f"  {R}FAIL: {raw[:60]}{RESET}")

        if raw == "No data found" or raw == "No results found":
            errors.append("Source returned no relevant data")
            print(f"  {R}FAIL: no relevant data in source{RESET}")

    is_valid = len(errors) == 0
    retry_count = state.get("retry_count", 0)

    if is_valid:
        print(f"  {G}PASS{RESET} -> routing to mapper")
    else:
        new_retry = retry_count + 1
        if new_retry >= MAX_RETRIES:
            print(f"  {R}FAIL (retry {new_retry}/{MAX_RETRIES}) -> exhausted{RESET}")
        else:
            print(f"  {Y}FAIL (retry {new_retry}/{MAX_RETRIES}) -> retrying{RESET}")

    return {
        **state,
        "is_valid": is_valid,
        "validation_errors": errors,
        "retry_count": retry_count + (0 if is_valid else 1),
    }


def should_retry(state: PipelineState) -> str:
    """Conditional edge: decide where to route after validation."""
    if state.get("is_valid", False):
        return "mapper"
    if state.get("retry_count", 0) >= MAX_RETRIES:
        return "exhausted"
    return "retry"
