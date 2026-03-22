"""Data Quality Validation Agent - scores nurtured + associated data 0-100."""

from __future__ import annotations

import json
import re
from datetime import datetime

from agents.llm import get_llm
from storage.source_store import save_quality_review


# ── Quality check tools (deterministic) ──────────────────────────────────────

def detect_missing_values(nurtured: dict) -> dict:
    """Check for missing or empty fields in nurtured data."""
    issues = []
    severity = 0

    if not nurtured.get("title"):
        issues.append("Missing title")
        severity += 10
    if not nurtured.get("summary"):
        issues.append("Missing summary")
        severity += 10
    if not nurtured.get("data_points"):
        issues.append("No data points extracted")
        severity += 25
    else:
        for i, dp in enumerate(nurtured["data_points"]):
            if not dp.get("value"):
                issues.append(f"Data point {i+1} ({dp.get('label', '?')}) has no value")
                severity += 10
            if not dp.get("label"):
                issues.append(f"Data point {i+1} has no label")
                severity += 5
    if not nurtured.get("raw_clean_text"):
        issues.append("No clean text content")
        severity += 15

    return {"tool": "missing_values", "issues": issues, "severity": min(severity, 50)}


def flag_anomalies(nurtured: dict, associations: list[dict]) -> dict:
    """Flag anomalies: mismatched associations, suspicious data."""
    issues = []
    severity = 0

    # No associations at all
    if not associations:
        issues.append("Source not associated with any initiative")
        severity += 20

    # Low confidence associations
    low_conf = [a for a in associations if a.get("confidence") == "low"]
    if low_conf:
        names = [a.get("initiative_name", a.get("initiative_id", "?")) for a in low_conf]
        issues.append(f"Low confidence associations: {', '.join(names)}")
        severity += 10 * len(low_conf)

    # Data points without dates could be stale
    data_points = nurtured.get("data_points", [])
    undated = [dp for dp in data_points if not dp.get("date")]
    if undated and data_points:
        pct = len(undated) / len(data_points) * 100
        if pct > 50:
            issues.append(f"{len(undated)}/{len(data_points)} data points have no date — may be stale")
            severity += 10

    # Very short clean text suggests poor extraction
    clean_text = nurtured.get("raw_clean_text", "")
    if clean_text and len(clean_text) < 100:
        issues.append(f"Clean text is very short ({len(clean_text)} chars) — possible extraction issue")
        severity += 15

    return {"tool": "anomalies", "issues": issues, "severity": min(severity, 40)}


def calculate_errors(nurtured: dict) -> dict:
    """Check for numerical inconsistencies and calculation errors."""
    issues = []
    severity = 0

    data_points = nurtured.get("data_points", [])
    values = []

    for dp in data_points:
        val_str = str(dp.get("value", ""))
        nums = re.findall(r"[-+]?\d*\.?\d+", val_str.replace(",", ""))
        if nums:
            try:
                values.append((dp.get("label", ""), float(nums[0]), val_str))
            except ValueError:
                pass

    # Check for negative values where they shouldn't exist
    for label, num, raw in values:
        label_lower = label.lower()
        if num < 0 and any(kw in label_lower for kw in ["rate", "count", "total", "number", "population", "units"]):
            issues.append(f"Negative value for '{label}': {raw}")
            severity += 15

    # Check for unreasonably large percentages
    for label, num, raw in values:
        if "%" in raw and num > 100:
            issues.append(f"Percentage over 100% for '{label}': {raw}")
            severity += 10

    # Check if tables have inconsistent row lengths
    for tbl in nurtured.get("tables", []):
        headers = tbl.get("headers", [])
        rows = tbl.get("rows", [])
        if headers:
            for i, row in enumerate(rows):
                if len(row) != len(headers):
                    issues.append(f"Table '{tbl.get('name', '?')}' row {i+1} has {len(row)} cols, expected {len(headers)}")
                    severity += 5

    return {"tool": "calculation_errors", "issues": issues, "severity": min(severity, 30)}


def format_inconsistencies(nurtured: dict) -> dict:
    """Detect formatting inconsistencies in the data."""
    issues = []
    severity = 0

    data_points = nurtured.get("data_points", [])

    # Mixed date formats
    date_formats = set()
    for dp in data_points:
        date_str = dp.get("date", "")
        if not date_str:
            continue
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            date_formats.add("ISO")
        elif re.match(r"\d{1,2}/\d{1,2}/\d{2,4}", date_str):
            date_formats.add("US")
        elif re.match(r"\d{4}", date_str):
            date_formats.add("year_only")
        else:
            date_formats.add("other")

    if len(date_formats) > 1:
        issues.append(f"Mixed date formats detected: {', '.join(date_formats)}")
        severity += 10

    # Mixed number formats (some with commas, some without)
    has_comma = False
    no_comma = False
    for dp in data_points:
        val = str(dp.get("value", ""))
        nums = re.findall(r"\d[\d,]*\.?\d*", val)
        for n in nums:
            if "," in n:
                has_comma = True
            elif len(n.replace(".", "")) > 3:
                no_comma = True
    if has_comma and no_comma:
        issues.append("Inconsistent number formatting (some use commas, some don't)")
        severity += 5

    # Check for encoding artifacts
    clean_text = nurtured.get("raw_clean_text", "")
    encoding_markers = ["â€", "Ã", "Â", "\ufffd", "\\u00"]
    for marker in encoding_markers:
        if marker in clean_text:
            issues.append(f"Encoding artifact detected: '{marker}'")
            severity += 10
            break

    return {"tool": "format_inconsistencies", "issues": issues, "severity": min(severity, 25)}


def detect_outliers(nurtured: dict) -> dict:
    """Detect statistical outliers in numerical data points."""
    issues = []
    severity = 0

    data_points = nurtured.get("data_points", [])

    # Group numeric values
    values = []
    for dp in data_points:
        val_str = str(dp.get("value", "")).replace(",", "")
        nums = re.findall(r"[-+]?\d*\.?\d+", val_str)
        if nums:
            try:
                values.append((dp.get("label", ""), float(nums[0])))
            except ValueError:
                pass

    if len(values) >= 3:
        nums_only = [v for _, v in values]
        mean = sum(nums_only) / len(nums_only)
        variance = sum((x - mean) ** 2 for x in nums_only) / len(nums_only)
        std = variance ** 0.5

        if std > 0:
            for label, val in values:
                z_score = abs(val - mean) / std
                if z_score > 3:
                    issues.append(f"Outlier detected: '{label}' = {val} (z-score: {z_score:.1f})")
                    severity += 10

    # Check for values that are exactly 0 which might indicate missing data
    for dp in data_points:
        val_str = str(dp.get("value", ""))
        if val_str.strip() in ("0", "0.0", "0%"):
            label = dp.get("label", "?")
            issues.append(f"Zero value for '{label}' — may indicate missing data")
            severity += 5

    return {"tool": "outliers", "issues": issues, "severity": min(severity, 30)}


# ── Main validation function ─────────────────────────────────────────────────

ALL_CHECKS = [
    detect_missing_values,
    flag_anomalies,
    calculate_errors,
    format_inconsistencies,
    detect_outliers,
]


def validate_quality(url: str, nurtured: dict, associations: list[dict]) -> dict:
    """Run all quality checks and produce a 0-100 score.

    Returns:
        Dict with url, score, passed, issues list, and per-tool results.
    """
    results = []
    total_severity = 0

    for check in ALL_CHECKS:
        if check == flag_anomalies:
            result = check(nurtured, associations)
        else:
            result = check(nurtured)
        results.append(result)
        total_severity += result["severity"]

    # Score: 100 minus total severity, clamped to 0-100
    score = max(0, min(100, 100 - total_severity))

    # Collect all issues
    all_issues = []
    for r in results:
        for issue in r["issues"]:
            all_issues.append({
                "tool": r["tool"],
                "issue": issue,
                "severity": r["severity"],
            })

    # Use LLM for a final qualitative assessment if there are issues
    llm_assessment = ""
    if all_issues:
        llm_assessment = _llm_assess(url, nurtured, associations, all_issues, score)

    # Categorize: gold (100-70), review (70-30), drop (< 30)
    if score >= 70:
        tier = "gold"
    elif score >= 30:
        tier = "review"
    else:
        tier = "drop"

    output = {
        "url": url,
        "score": score,
        "tier": tier,
        "issue_count": len(all_issues),
        "issues": all_issues,
        "tool_results": results,
        "llm_assessment": llm_assessment,
    }

    # Only persist gold and review — drop gets discarded
    if tier != "drop":
        save_quality_review(
            url=url,
            score=score,
            tier=tier,
            issues=all_issues,
            nurtured=nurtured,
            associations=associations,
        )

    return output


def _llm_assess(
    url: str,
    nurtured: dict,
    associations: list[dict],
    issues: list[dict],
    score: int,
) -> str:
    """Get a brief LLM assessment of the quality issues."""
    llm = get_llm()

    issues_text = "\n".join(f"- [{i['tool']}] {i['issue']}" for i in issues)
    assoc_text = ", ".join(a.get("initiative_id", "?") for a in associations) or "none"

    result = llm.invoke([
        ("system", "You are a data quality reviewer. Give a 2-3 sentence assessment of the data quality issues. Be direct and specific about what needs fixing."),
        ("user", f"URL: {url}\nScore: {score}/100\nAssociated initiatives: {assoc_text}\n\nIssues:\n{issues_text}"),
    ])
    return result.content
