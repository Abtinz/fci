"""Streamlit page: full pipeline fetch → nurture → associate → quality validate."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from data.sources import PREDEFINED_SOURCES
from tools.crawler import fetch_source
from agents.nurture import nurture_content
from agents.associate import associate_content
from agents.quality import validate_quality
from storage.source_store import list_quality_reviews, mongo_configured

st.set_page_config(page_title="Quality Validation", page_icon="V1M", layout="wide")
st.title("Quality Validation")
st.caption("Fetch → Nurture → Associate → Validate (scored 0-100). Gold (70-100) and Review (30-69) are stored. Below 30 is dropped.")

tab_run, tab_history = st.tabs(["Run Validation", "Review History"])

with tab_run:
    url = st.text_input("URL", placeholder="https://example.com/report.pdf")

    predef = st.selectbox(
        "Or pick a predefined source",
        options=[""] + PREDEFINED_SOURCES,
        format_func=lambda x: x if x else "— select —",
    )
    if predef and not url:
        url = predef

    run = st.button("Run Full Pipeline", type="primary", disabled=not url)

    if run and url:
        with st.spinner("1/4 Fetching..."):
            try:
                raw = fetch_source.invoke({"url": url})
            except Exception as exc:
                st.error(f"Fetch failed: {exc}")
                st.stop()

        with st.spinner("2/4 Nurturing..."):
            try:
                nurtured = nurture_content(url, raw)
            except Exception as exc:
                st.error(f"Nurture failed: {exc}")
                st.stop()

        with st.spinner("3/4 Associating..."):
            try:
                assoc_result = associate_content(url, nurtured)
                associations = assoc_result.get("associations", [])
            except Exception as exc:
                st.error(f"Association failed: {exc}")
                st.stop()

        with st.spinner("4/4 Validating quality..."):
            try:
                result = validate_quality(url, nurtured, associations)
            except Exception as exc:
                st.error(f"Validation failed: {exc}")
                st.stop()

        score = result["score"]
        tier = result["tier"]

        # Tier display
        tier_config = {
            "gold": {"color": "green", "label": "GOLD", "icon": "trophy", "desc": "Stored — high quality"},
            "review": {"color": "orange", "label": "REVIEW", "icon": "warning", "desc": "Stored — needs human review"},
            "drop": {"color": "red", "label": "DROPPED", "icon": "x", "desc": "Not stored — too low quality"},
        }
        tc = tier_config[tier]

        col1, col2, col3 = st.columns(3)
        col1.metric("Quality Score", f"{score}/100")
        col2.metric("Tier", tc["label"])
        col3.metric("Issues", result["issue_count"])

        if tier == "gold":
            st.success(f":{tc['icon']}: **{tc['label']}** — {tc['desc']}")
        elif tier == "review":
            st.warning(f":{tc['icon']}: **{tc['label']}** — {tc['desc']}")
        else:
            st.error(f":{tc['icon']}: **{tc['label']}** — {tc['desc']}")

        st.progress(score / 100)

        if result.get("llm_assessment"):
            st.subheader("Assessment")
            st.info(result["llm_assessment"])

        st.subheader("Quality Checks")
        tool_labels = {
            "missing_values": "Missing Values",
            "anomalies": "Anomalies",
            "calculation_errors": "Calculation Errors",
            "format_inconsistencies": "Format Inconsistencies",
            "outliers": "Outliers",
        }

        for tr in result["tool_results"]:
            tool_name = tool_labels.get(tr["tool"], tr["tool"])
            issue_count = len(tr["issues"])
            sev = tr["severity"]

            if issue_count == 0:
                st.markdown(f":white_check_mark: **{tool_name}** — no issues")
            else:
                st.markdown(f":x: **{tool_name}** — {issue_count} issue(s) (severity: {sev})")
                for issue in tr["issues"]:
                    st.markdown(f"  - {issue}")

        with st.expander(f"Associations ({len(associations)})"):
            if not associations:
                st.warning("No initiative associations.")
            for a in associations:
                conf = a.get("confidence", "?")
                st.markdown(f"- **{a.get('initiative_id', '')}** {a.get('initiative_name', '')} — confidence: {conf}")

        with st.expander("Nurtured data"):
            if nurtured.get("title"):
                st.markdown(f"**{nurtured['title']}**")
            if nurtured.get("data_points"):
                for dp in nurtured["data_points"]:
                    date_str = f" ({dp['date']})" if dp.get("date") else ""
                    st.markdown(f"- **{dp.get('label', '')}**: {dp.get('value', '')}{date_str}")

        with st.expander("Full validation result"):
            st.json(result)


with tab_history:
    if not mongo_configured():
        st.warning("MongoDB not configured — no history available.")
    else:
        filter_tier = st.selectbox("Filter by tier", ["All", "Gold (70-100)", "Review (30-69)"], key="hist_filter")
        tier_filter = None
        if filter_tier.startswith("Gold"):
            tier_filter = "gold"
        elif filter_tier.startswith("Review"):
            tier_filter = "review"

        reviews = list_quality_reviews(tier=tier_filter)

        # Summary
        gold_count = sum(1 for r in reviews if r.get("tier") == "gold") if not tier_filter else (len(reviews) if tier_filter == "gold" else 0)
        review_count = sum(1 for r in reviews if r.get("tier") == "review") if not tier_filter else (len(reviews) if tier_filter == "review" else 0)

        col_a, col_b = st.columns(2)
        col_a.metric(":trophy: Gold", gold_count if not tier_filter else len(reviews) if tier_filter == "gold" else "-")
        col_b.metric(":warning: Review", review_count if not tier_filter else len(reviews) if tier_filter == "review" else "-")

        st.subheader(f"Reviews ({len(reviews)})")

        for rev in reviews:
            score = rev.get("score", 0)
            tier = rev.get("tier", "?")
            icon = ":trophy:" if tier == "gold" else ":warning:"
            with st.expander(f"{icon} **{score}/100** [{tier.upper()}] — {rev.get('url', '')[:80]}"):
                st.markdown(f"**Title:** {rev.get('nurtured_title', '')}")
                st.markdown(f"**Summary:** {rev.get('nurtured_summary', '')}")

                assocs = rev.get("associations", [])
                if assocs:
                    st.markdown("**Associations:** " + ", ".join(
                        f"{a.get('initiative_id', '?')} ({a.get('confidence', '?')})" for a in assocs
                    ))

                issues = rev.get("issues", [])
                if issues:
                    st.markdown(f"**Issues ({len(issues)}):**")
                    for iss in issues:
                        st.markdown(f"- [{iss.get('tool', '')}] {iss.get('issue', '')}")

                st.caption(f"Reviewed: {rev.get('reviewed_at', '')}")
