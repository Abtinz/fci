"""FastAPI service exposing discovery and source-store operations."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ui.discovery import (
    DEFAULT_SECTION_INITIATIVES,
    get_discovered_sources,
    get_human_predefined_sources,
    get_mongo_connection_status,
    is_mongo_configured,
    run_discovery_batch,
    run_discovery_step,
    run_tavily_only_batch,
    run_tavily_only_search,
    save_human_predefined_source,
)


class InitiativeRequest(BaseModel):
    initiative_id: str
    category: str
    name: str
    metric_label: str
    target_value: str


class TavilySearchRequest(InitiativeRequest):
    max_results: int = Field(default=5, ge=1, le=10)


class HumanPredefinedSourceRequest(InitiativeRequest):
    url: str
    source_type: str
    description: str
    notes: str = ""


app = FastAPI(
    title="Vision One Million API",
    version="0.1.0",
    description="API for discovery, Tavily search, and source management.",
)


@app.get("/health")
def health() -> dict:
    mongo_ok, mongo_message = get_mongo_connection_status()
    return {
        "status": "ok",
        "mongo_configured": is_mongo_configured(),
        "mongo_ok": mongo_ok,
        "mongo_message": mongo_message,
    }


@app.get("/sections")
def get_sections() -> list[dict[str, str]]:
    return DEFAULT_SECTION_INITIATIVES


@app.post("/discovery/run")
def discovery_run(request: InitiativeRequest) -> dict:
    return run_discovery_step(
        initiative_id=request.initiative_id,
        category=request.category,
        name=request.name,
        metric_label=request.metric_label,
        target_value=request.target_value,
    )


@app.post("/discovery/all-sections")
def discovery_all_sections() -> list[dict]:
    return run_discovery_batch()


@app.post("/discovery/tavily-only")
def discovery_tavily_only(request: TavilySearchRequest) -> dict:
    return run_tavily_only_search(
        initiative_id=request.initiative_id,
        category=request.category,
        name=request.name,
        metric_label=request.metric_label,
        target_value=request.target_value,
        max_results=request.max_results,
    )


@app.post("/discovery/tavily-only/all-sections")
def discovery_tavily_only_all_sections(max_results: int = 5) -> list[dict]:
    return run_tavily_only_batch(max_results=max_results)


@app.get("/sources/discovered")
def sources_discovered(initiative_id: str | None = None, limit: int = 100) -> list[dict]:
    return get_discovered_sources(initiative_id=initiative_id, limit=limit)


@app.get("/sources/predefined")
def sources_predefined(initiative_id: str | None = None) -> list[dict]:
    return get_human_predefined_sources(initiative_id=initiative_id)


@app.post("/sources/predefined")
def create_predefined_source(request: HumanPredefinedSourceRequest) -> dict:
    try:
        return save_human_predefined_source(
            initiative_id=request.initiative_id,
            category=request.category,
            name=request.name,
            metric_label=request.metric_label,
            target_value=request.target_value,
            url=request.url,
            source_type=request.source_type,
            description=request.description,
            notes=request.notes,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
