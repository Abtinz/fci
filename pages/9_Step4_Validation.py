"""Streamlit page for testing the validation agent in isolation."""

from __future__ import annotations

import streamlit as st

from agents.validation import run_validation, VALIDATION_CRITERIA
from tools.playwright_checker import check_source_with_playwright
from ui.discovery import get_mongo_connection_status, is_mongo_configured
from ui.extraction import get_saved_extractions


st.set_page_config(page_title="Step 4 · Validation", page_icon="V1M", layout="wide")

st.title("Step 4 · Validation")
st.caption("Test the validation node: deterministic checks + Playwright source verification.")

if not is_mongo_configured():
    st.error("MongoDB is not configured. Set MONGODB_URI and MONGODB_DB in .env.")
    st.stop()

ok, status_msg = get_mongo_connection_status()
if not ok:
    st.error(f"MongoDB connection issue: {status_msg}")
    st.stop()

tab_full, tab_playwright = st.tabs(["Full Validation", "Playwright Only"])

# ── Tab 1: Full validation from saved extractions ────────────────────────────
with tab_full:
    st.subheader("Validate saved extractions")

    extractions = get_saved_extractions(limit=200)

    if not extractions:
        st.warning("No saved extractions found. Run Step 3 first.")
        st.stop()

    # Group by initiative
    initiatives = {}
    for ext in extractions:
        key = ext.get("initiative_id") or ext.get("name", "unknown")
        name = ext.get("name", key)
        if key not in initiatives:
            initiatives[key] = {"name": name, "extractions": []}
        initiatives[key]["extractions"].append(ext)

    selected_key = st.selectbox(
        "Select initiative",
        options=list(initiatives.keys()),
        format_func=lambda k: f"{initiatives[k]['name']} ({len(initiatives[k]['extractions'])} extractions)",
    )

    selected = initiatives[selected_key]
    extracted_items = []
    for ext in selected["extractions"]:
        extracted_items.append({
            "raw_value": ext.get("raw_value", ""),
            "numeric_value": ext.get("numeric_value"),
            "unit": ext.get("unit", ""),
            "context": ext.get("context", ""),
            "source_url": ext.get("url", ""),
        })

    with st.expander("Extraction data to validate"):
        st.json(extracted_items)

    if st.button("Run Validation", type="primary"):
        state = {
            "initiative": {"name": selected["name"]},
            "extracted": extracted_items,
            "retry_count": 0,
        }

        with st.spinner("Running validation..."):
            result = run_validation(state)

        if result.get("is_valid"):
            st.success("PASS — all checks passed")
        else:
            st.error("FAIL — validation errors found")

        errors = result.get("validation_errors", [])
        if errors:
            for err in errors:
                st.warning(err)

        st.json({
            "is_valid": result.get("is_valid"),
            "validation_errors": result.get("validation_errors"),
            "retry_count": result.get("retry_count"),
        })

# ── Tab 2: Playwright-only check ─────────────────────────────────────────────
with tab_playwright:
    st.subheader("Test Playwright source check directly")

    url = st.text_input("Source URL to check", value="https://example.com")

    st.markdown("**Criteria** (checked against page content):")
    st.json(VALIDATION_CRITERIA)

    custom_expected = st.text_input(
        "Custom expected text (leave empty to use default criteria)",
        value="",
    )

    if st.button("Run Playwright Check", type="primary"):
        if custom_expected:
            criteria = [{"field": "custom", "expected": custom_expected}]
        else:
            criteria = VALIDATION_CRITERIA

        with st.spinner(f"Visiting {url} with Playwright..."):
            result = check_source_with_playwright(url, criteria)

        if result.get("error"):
            st.error(f"Page error: {result['error']}")
        elif result.get("passed"):
            st.success("PASS — all criteria found on page")
        else:
            st.error("FAIL — some criteria not found")

        for r in result.get("results", []):
            if r.get("found"):
                st.success(f"'{r['field']}': found")
            else:
                msg = r.get("error", f"expected '{r['expected']}' not found")
                st.warning(f"'{r['field']}': {msg}")
                if r.get("snippet"):
                    with st.expander("Page snippet"):
                        st.text(r["snippet"])

        if result.get("page_title"):
            st.caption(f"Page title: {result['page_title']}")
