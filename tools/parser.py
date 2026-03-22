"""Data parsing and transformation tools."""

from __future__ import annotations

import json
import re
from langchain_core.tools import tool


@tool
def parse_number(text: str) -> str:
    """Extract the first number from a text string.
    Use this to pull a numeric value from messy text data.
    Returns the number as a string, or 'No number found'.
    """
    match = re.search(r"[-+]?\d*\.?\d+", text.replace(",", ""))
    if match:
        return match.group()
    return "No number found"


@tool
def compare_to_target(value: str, target: str) -> str:
    """Compare an extracted numeric value against a target value.
    Use this to determine if a metric meets its target.
    Returns a comparison summary.
    Args:
        value: The extracted value (e.g., '4.1%')
        target: The target value (e.g., '3% Vacancy rate')
    """
    def extract_num(s: str) -> float | None:
        match = re.search(r"[-+]?\d*\.?\d+", s.replace(",", ""))
        return float(match.group()) if match else None

    v = extract_num(value)
    t = extract_num(target)

    if v is None:
        return f"Could not parse value: {value}"
    if t is None:
        return f"Could not parse target: {target}"

    diff = v - t
    pct = (diff / t * 100) if t != 0 else 0

    if abs(diff) < 0.001:
        relation = "exactly meets"
    elif diff > 0:
        relation = "exceeds"
    else:
        relation = "falls short of"

    return (
        f"Value: {v}, Target: {t}\n"
        f"The value {relation} the target by {abs(diff):.2f} ({abs(pct):.1f}%)"
    )


@tool
def format_scorecard_entry(
    initiative_id: str,
    status: str,
    reasoning: str,
    raw_value: str,
    source_url: str,
) -> str:
    """Format a scorecard initiative result as structured JSON.
    Use this as the final step to produce the output for one initiative.
    Returns a JSON string.
    """
    entry = {
        "id": initiative_id,
        "status": status,
        "reasoning": reasoning,
        "extracted_value": raw_value,
        "source_url": source_url,
    }
    return json.dumps(entry, indent=2)
