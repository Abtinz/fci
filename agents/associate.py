"""Association Agent - maps nurtured content to scorecard initiatives."""

from __future__ import annotations

import json

from agents.llm import get_llm
from data.sources import SCORECARD_INITIATIVES


def _format_knowledge_base() -> str:
    lines = []
    for init in SCORECARD_INITIATIVES:
        lines.append(
            f"- [{init['id']}] {init['category']} > {init['name']} | "
            f"Metric: {init['metric_label']} | Target: {init['target_value']}"
        )
    return "\n".join(lines)


SYSTEM = """You are an association agent. You receive nurtured (cleaned) data from a web source
and a knowledge base of scorecard initiatives. Your job is to map the source data to
the most relevant initiative(s).

KNOWLEDGE BASE:
{knowledge_base}

RULES:
- A source can map to ONE OR MORE initiatives if it contains relevant data for each.
- Only associate if the source actually contains data, metrics, or information that
  could be used to measure or track the initiative's metric.
- Do NOT associate based on vague topical overlap — the source must have actionable data.
- For each association, explain WHY this source is relevant to that initiative and
  which specific data points from the source support the metric.
- Rate your confidence: "high", "medium", or "low".

OUTPUT FORMAT:
Return a JSON object:
{{
  "associations": [
    {{
      "initiative_id": "housing-1",
      "category": "Housing",
      "initiative_name": "Building the homes we need",
      "metric_label": "Dwellings built",
      "confidence": "high",
      "reasoning": "Source contains housing starts data for 2024 (73,617 starts)",
      "relevant_data_points": ["73,617 housing starts in 2024", "94,908 new homes created"]
    }}
  ]
}}

If the source does not clearly relate to any initiative, return:
{{"associations": []}}

Return ONLY valid JSON. No markdown, no explanation."""


def _parse_json(content: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        try:
            return json.loads(content.strip())
        except (json.JSONDecodeError, TypeError):
            return {"associations": []}


def associate_content(url: str, nurtured: dict) -> dict:
    """Map nurtured content to scorecard initiatives.

    Args:
        url: The source URL.
        nurtured: Output from nurture_content().

    Returns:
        Dict with "url", "associations" list, and the original "nurtured" data.
    """
    llm = get_llm()

    prompt = SYSTEM.format(knowledge_base=_format_knowledge_base())

    # Build a concise representation of the nurtured data for the LLM
    source_summary = json.dumps({
        "url": url,
        "title": nurtured.get("title", ""),
        "summary": nurtured.get("summary", ""),
        "data_points": nurtured.get("data_points", []),
        "tables": [{"name": t.get("name", ""), "headers": t.get("headers", [])} for t in nurtured.get("tables", [])],
        "data_links": nurtured.get("data_links", []),
    }, indent=2)

    result = llm.invoke([
        ("system", prompt),
        ("user", f"Associate this nurtured source data to the relevant initiatives:\n\n{source_summary}"),
    ])

    parsed = _parse_json(result.content)

    return {
        "url": url,
        "associations": parsed.get("associations", []),
        "nurtured": nurtured,
    }


def associate_batch(nurtured_sources: dict[str, dict]) -> dict[str, dict]:
    """Associate multiple nurtured sources. Input: {url: nurtured_data}. Output: {url: association_result}."""
    results = {}
    for url, nurtured in nurtured_sources.items():
        results[url] = associate_content(url, nurtured)
    return results
