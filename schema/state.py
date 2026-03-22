"""Pipeline state definitions."""

from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field

Status = Literal[
    "ACHIEVED", "ON_TRACK", "IN_PROGRESS", "NEEDS_ATTENTION", "NO_ASSESSMENT"
]


class Initiative(BaseModel):
    id: str
    category: str
    name: str
    metric_label: str
    target_value: str


class DataSource(BaseModel):
    url: str
    source_type: Literal["api", "html", "pdf", "csv", "xlsx"] = "html"
    description: str = ""
    is_predefined: bool = False


class ExtractedData(BaseModel):
    raw_value: str = ""
    numeric_value: float | None = None
    unit: str = ""
    source_url: str = ""
    context: str = ""


class ValidationResult(BaseModel):
    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)


class ScorecardResult(BaseModel):
    initiative: Initiative
    sources: list[DataSource] = Field(default_factory=list)
    extracted: list[ExtractedData] = Field(default_factory=list)
    validation: ValidationResult = Field(default_factory=ValidationResult)
    status: Status = "NO_ASSESSMENT"
    status_reasoning: str = ""
    retry_count: int = 0
    error: str = ""
