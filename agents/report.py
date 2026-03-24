"""Report Agent - aggregates validated data into a scorecard report."""

from __future__ import annotations

import json
from typing import Any

from agents.llm import get_llm
from data.sources import SCORECARD_INITIATIVES, SCORECARD_CATEGORIES, INITIATIVES_BY_ID
from storage.source_store import list_quality_reviews


STATUS_LABELS = {
    "ACHIEVED": {"label": "Achieved", "color": "#22c55e", "score": 100},
    "ON_TRACK": {"label": "On Track", "color": "#3b82f6", "score": 80},
    "IN_PROGRESS": {"label": "In Progress", "color": "#f59e0b", "score": 60},
    "NEEDS_ATTENTION": {"label": "Needs Attention", "color": "#ef4444", "score": 30},
    "NO_DATA": {"label": "No Data", "color": "#6b7280", "score": 0},
}


def _gather_data() -> dict[str, list[dict]]:
    """Pull all gold + review tier data from Mongo, grouped by initiative_id."""
    gold = list_quality_reviews(tier="gold")
    review = list_quality_reviews(tier="review")

    by_initiative: dict[str, list[dict]] = {}
    for item in gold + review:
        for assoc in item.get("associations", []):
            init_id = assoc.get("initiative_id", "")
            if init_id:
                if init_id not in by_initiative:
                    by_initiative[init_id] = []
                by_initiative[init_id].append({
                    "url": item.get("url", ""),
                    "score": item.get("score", 0),
                    "tier": item.get("tier", ""),
                    "title": item.get("nurtured_title", ""),
                    "summary": item.get("nurtured_summary", ""),
                    "confidence": assoc.get("confidence", ""),
                    "reasoning": assoc.get("reasoning", ""),
                    "data_points": assoc.get("relevant_data_points", []),
                    "issues": item.get("issues", []),
                })

    return by_initiative


def _assess_initiative(initiative: dict, sources: list[dict]) -> dict:
    """Use LLM to assess an initiative's status based on its associated sources."""
    if not sources:
        return {
            "status": "NO_DATA",
            "reasoning": "No validated data sources available.",
            "value": "",
            "highlights": [],
            "source_count": 0,
            "sources": [],
        }

    llm = get_llm()

    sources_text = json.dumps([{
        "url": s["url"],
        "title": s["title"],
        "summary": s["summary"],
        "quality_score": s["score"],
        "tier": s["tier"],
        "confidence": s["confidence"],
        "data_points": s["data_points"],
    } for s in sources], indent=2)

    result = llm.invoke([
        ("system", """You assess scorecard initiative status based on available data sources.

Return a JSON object:
{
  "status": "ACHIEVED" | "ON_TRACK" | "IN_PROGRESS" | "NEEDS_ATTENTION" | "NO_DATA",
  "reasoning": "2-3 sentence explanation",
  "value": "The most relevant current metric value found (e.g. '4.1%', '73,617 units')",
  "highlights": ["key finding 1", "key finding 2"]
}

Definitions:
- ACHIEVED: metric has met or exceeded the target
- ON_TRACK: metric is progressing toward the target and likely to meet it
- IN_PROGRESS: work is underway but unclear if target will be met
- NEEDS_ATTENTION: metric is falling short or trending negatively
- NO_DATA: insufficient data to assess

Return ONLY valid JSON."""),
        ("user", f"""Initiative: {initiative['name']}
Category: {initiative['category']}
Metric: {initiative['metric_label']}
Target: {initiative['target_value']}

Available sources ({len(sources)}):
{sources_text}"""),
    ])

    try:
        parsed = json.loads(result.content)
    except (json.JSONDecodeError, TypeError):
        content = result.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        try:
            parsed = json.loads(content.strip())
        except (json.JSONDecodeError, TypeError):
            parsed = {"status": "NO_DATA", "reasoning": result.content, "value": "", "highlights": []}

    return {
        "status": parsed.get("status", "NO_DATA"),
        "reasoning": parsed.get("reasoning", ""),
        "value": parsed.get("value", ""),
        "highlights": parsed.get("highlights", []),
        "source_count": len(sources),
        "sources": sources,
    }


def generate_report() -> dict[str, Any]:
    """Generate the full scorecard report from validated data.

    Returns:
        Dict with categories, initiatives, overall stats, and per-initiative assessments.
    """
    data_by_initiative = _gather_data()

    categories = []
    all_initiatives = []
    total_assessed = 0
    status_counts = {s: 0 for s in STATUS_LABELS}

    for cat in SCORECARD_CATEGORIES:
        cat_initiatives = []
        cat_scores = []

        for init_id in cat["initiative_ids"]:
            initiative = INITIATIVES_BY_ID.get(init_id)
            if not initiative:
                continue

            sources = data_by_initiative.get(init_id, [])
            assessment = _assess_initiative(initiative, sources)

            status = assessment["status"]
            status_info = STATUS_LABELS.get(status, STATUS_LABELS["NO_DATA"])
            status_counts[status] = status_counts.get(status, 0) + 1

            if status != "NO_DATA":
                total_assessed += 1
                cat_scores.append(status_info["score"])

            init_result = {
                "id": init_id,
                "name": initiative["name"],
                "category": initiative["category"],
                "metric_label": initiative["metric_label"],
                "target_value": initiative["target_value"],
                "status": status,
                "status_label": status_info["label"],
                "status_color": status_info["color"],
                "value": assessment["value"],
                "reasoning": assessment["reasoning"],
                "highlights": assessment["highlights"],
                "source_count": assessment["source_count"],
                "sources": assessment["sources"],
            }

            cat_initiatives.append(init_result)
            all_initiatives.append(init_result)

        cat_score = round(sum(cat_scores) / len(cat_scores)) if cat_scores else 0

        categories.append({
            "id": cat["id"],
            "name": cat["name"],
            "score": cat_score,
            "initiative_count": len(cat_initiatives),
            "assessed_count": sum(1 for i in cat_initiatives if i["status"] != "NO_DATA"),
            "initiatives": cat_initiatives,
        })

    overall_scores = [STATUS_LABELS[i["status"]]["score"] for i in all_initiatives if i["status"] != "NO_DATA"]
    overall_score = round(sum(overall_scores) / len(overall_scores)) if overall_scores else 0

    return {
        "overall_score": overall_score,
        "total_initiatives": len(all_initiatives),
        "total_assessed": total_assessed,
        "status_counts": status_counts,
        "categories": categories,
        "initiatives": all_initiatives,
    }
