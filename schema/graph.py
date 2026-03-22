"""LangGraph state definition for the orchestrator."""

from __future__ import annotations

from typing import TypedDict
from schema.state import DataSource, ExtractedData, Status, Initiative


class PipelineState(TypedDict, total=False):
    """State flowing through the LangGraph pipeline for one initiative."""
    initiative: dict  # Initiative as dict for LangGraph serialization

    # Discovery
    sources: list[dict]

    # Extraction
    extracted: list[dict]

    # Validation
    is_valid: bool
    validation_errors: list[str]
    retry_count: int

    # Mapper
    status: str
    status_reasoning: str

    # Error
    error: str
