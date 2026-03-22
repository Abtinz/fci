"""Helpers for running the discovery step in isolation."""

from __future__ import annotations

from collections.abc import Callable

from dotenv import load_dotenv

from schema.graph import PipelineState
from schema.state import Initiative


load_dotenv()


DEFAULT_SECTION_INITIATIVES = [
    {
        "initiative_id": "housing-4",
        "category": "Housing",
        "name": "Rental vacancy rate",
        "metric_label": "Rental vacancy rate",
        "target_value": "3%",
    },
    {
        "initiative_id": "transportation-1",
        "category": "Transportation",
        "name": "Transit ridership",
        "metric_label": "Annual transit ridership",
        "target_value": "Increase year over year",
    },
    {
        "initiative_id": "healthcare-1",
        "category": "Healthcare",
        "name": "Emergency department wait times",
        "metric_label": "Median emergency department wait time",
        "target_value": "Decrease wait times",
    },
    {
        "initiative_id": "employment-1",
        "category": "Employment & Jobs",
        "name": "Unemployment rate",
        "metric_label": "Unemployment rate",
        "target_value": "Below provincial average",
    },
    {
        "initiative_id": "placemaking-1",
        "category": "placemaking & livability",
        "name": "Licensed childcare spaces",
        "metric_label": "Number of licensed childcare spaces",
        "target_value": "Increase supply",
    },
]


def build_discovery_state(
    initiative_id: str,
    category: str,
    name: str,
    metric_label: str,
    target_value: str,
) -> PipelineState:
    initiative = Initiative(
        id=initiative_id,
        category=category,
        name=name,
        metric_label=metric_label,
        target_value=target_value,
    )
    return {
        "initiative": initiative.model_dump(),
        "sources": [],
        "extracted": [],
        "is_valid": False,
        "validation_errors": [],
        "retry_count": 0,
        "status": "NO_ASSESSMENT",
        "status_reasoning": "",
        "error": "",
    }


def run_discovery_step(
    initiative_id: str,
    category: str,
    name: str,
    metric_label: str,
    target_value: str,
    runner: Callable[[PipelineState], PipelineState] | None = None,
) -> PipelineState:
    state = build_discovery_state(
        initiative_id=initiative_id,
        category=category,
        name=name,
        metric_label=metric_label,
        target_value=target_value,
    )
    if runner is None:
        from agents.discovery import run_discovery

        runner = run_discovery
    return runner(state)


def run_discovery_batch(
    initiatives: list[dict[str, str]] | None = None,
    runner: Callable[[PipelineState], PipelineState] | None = None,
) -> list[PipelineState]:
    batch = initiatives or DEFAULT_SECTION_INITIATIVES
    return [
        run_discovery_step(
            initiative_id=item["initiative_id"],
            category=item["category"],
            name=item["name"],
            metric_label=item["metric_label"],
            target_value=item["target_value"],
            runner=runner,
        )
        for item in batch
    ]
