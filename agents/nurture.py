"""Content Nurturing Agent - cleans raw extracted content into structured data."""

from __future__ import annotations

import json

from agents.llm import get_llm

SYSTEM = """You are a content nurturing agent. You receive raw extracted text from a web source
(HTML page, PDF, CSV, JSON, Excel) and your job is to clean it into a structured,
concise summary of the actual data and information on the page.

REMOVE:
- Navigation menus, headers, footers, sidebars
- Cookie notices, login prompts, JS warnings
- Boilerplate legal text, disclaimers
- Duplicate content, repeated headings
- "Skip to content", "Back to top", breadcrumbs
- Empty sections, placeholder text

KEEP:
- All numerical data, statistics, metrics, percentages
- Dates, time periods, reporting periods
- Named entities (organizations, programs, locations)
- Data tables (preserve structure)
- Key findings, conclusions, status updates
- Source attributions and methodology notes
- Links to downloadable data files

OUTPUT FORMAT:
Return a JSON object with these fields:
{
  "title": "Page/document title",
  "summary": "1-3 sentence summary of what this source contains",
  "data_points": [
    {"label": "metric name", "value": "value", "date": "reporting period if known"}
  ],
  "tables": [
    {"name": "table description", "headers": [...], "rows": [[...]]}
  ],
  "data_links": [
    {"url": "...", "label": "..."}
  ],
  "raw_clean_text": "The cleaned text content with all noise removed"
}

If there are no tables, return an empty list for "tables".
If there are no data links, return an empty list for "data_links".
If there are no clear data points, return an empty list for "data_points".
Always include "raw_clean_text" with the cleaned version of the full text.

Return ONLY valid JSON. No markdown, no explanation."""


def nurture_content(url: str, raw_content: str) -> dict:
    """Clean raw extracted content into structured data."""
    llm = get_llm()
    result = llm.invoke([
        ("system", SYSTEM),
        ("user", f"URL: {url}\n\nRAW CONTENT:\n{raw_content}"),
    ])

    try:
        return json.loads(result.content)
    except (json.JSONDecodeError, TypeError):
        # Try to extract JSON from markdown code blocks
        content = result.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        try:
            return json.loads(content.strip())
        except (json.JSONDecodeError, TypeError):
            return {
                "title": "",
                "summary": "",
                "data_points": [],
                "tables": [],
                "data_links": [],
                "raw_clean_text": result.content,
            }


def nurture_batch(sources: dict[str, str]) -> dict[str, dict]:
    """Nurture multiple sources. Input: {url: raw_content}. Output: {url: nurtured_data}."""
    results = {}
    for url, raw_content in sources.items():
        results[url] = nurture_content(url, raw_content)
    return results
