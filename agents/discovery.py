"""Source Discovery Agent - finds data sources for initiatives."""

from __future__ import annotations

import json
from datetime import date
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from agents.llm import get_llm
from tools.search import tavily_search, tavily_extract
from tools.crawler import check_url
from prompts.discovery import TASK, build_system_prompt
from schema.graph import PipelineState
from storage.source_store import get_predefined_sources, save_discovered_sources

# ── Colors ───────────────────────────────────────────────────────────────────
G = "\033[32m"; Y = "\033[33m"; R = "\033[31m"
DIM = "\033[2m"; BOLD = "\033[1m"; RESET = "\033[0m"


# ── Discovery-specific tools ────────────────────────────────────────────────

@tool
def lookup_predefined(initiative_id: str) -> str:
    """Look up a predefined data source for an initiative ID.
    Use this first before searching the web. Returns source details if found.
    """
    sources = get_predefined_sources(initiative_id)
    if sources:
        if len(sources) == 1:
            return json.dumps(sources[0], indent=2, default=str)
        return json.dumps(sources, indent=2, default=str)
    return f"No predefined source for {initiative_id}"


@tool
def format_discovery_result(url: str, source_type: str, description: str) -> str:
    """Format the final discovery result. Call this when you've found the best source.
    Args:
        url: The data source URL.
        source_type: One of 'api', 'html', 'pdf', 'csv', 'xlsx'.
        description: Brief description of what this source provides.
    """
    return json.dumps({
        "url": url,
        "source_type": source_type,
        "description": description,
    })


TOOLS = [lookup_predefined, tavily_search, tavily_extract, check_url, format_discovery_result]


def create_discovery_agent(current_date: str | None = None):
    prompt = build_system_prompt(current_date or date.today().isoformat())
    return create_react_agent(get_llm(), TOOLS, prompt=prompt)


# ── Node function for orchestrator ──────────────────────────────────────────

def run_discovery(state: PipelineState) -> PipelineState:
    """LangGraph node: run the discovery agent."""
    init = state["initiative"]
    retry = state.get("retry_count", 0)

    print(f"\n{G}{BOLD}[DISCOVERY]{RESET} {init['name']} {DIM}({init['id']}){RESET}")
    if retry > 0:
        print(f"  {Y}retry #{retry}{RESET}")

    retry_context = ""
    if retry > 0:
        errors = state.get("validation_errors", [])
        retry_context = f"Previous attempt failed with: {errors}. Try a different source."

    task = TASK.format(**init, retry_context=retry_context)
    agent = create_discovery_agent()
    result = agent.invoke({"messages": [("user", task)]})

    # Parse the last tool call result to get the source
    sources = []
    for msg in reversed(result["messages"]):
        if hasattr(msg, "content") and msg.content:
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, dict) and "url" in parsed:
                    sources = [parsed]
                    print(f"  {G}found{RESET} {DIM}{parsed.get('source_type','?')}{RESET} -> {parsed['url'][:80]}")
                    break
                elif isinstance(parsed, list):
                    sources = parsed
                    for s in sources:
                        print(f"  {G}found{RESET} {DIM}{s.get('source_type','?')}{RESET} -> {s.get('url','')[:80]}")
                    break
            except (json.JSONDecodeError, TypeError):
                continue

    if not sources:
        print(f"  {R}no sources found{RESET}")
    else:
        saved = save_discovered_sources(
            initiative=init,
            sources=sources,
            retry_count=retry,
        )
        if saved:
            print(f"  {DIM}saved {saved} source(s) to MongoDB{RESET}")

    return {**state, "sources": sources}
