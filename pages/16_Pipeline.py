"""Streamlit page: run the full pipeline — discovery + predefined → process all."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agents.pipeline import run_pipeline_all, collect_all_urls

st.set_page_config(page_title="Pipeline Runner", page_icon="V1M", layout="wide")
st.title("Pipeline Runner")
st.caption("Discovers dynamic sources + predefined sources, then runs Fetch → Nurture → Associate → Validate on all of them.")

skip_discovery = st.checkbox("Skip discovery (predefined only)", value=False)

# Preview sources
if st.button("Preview sources"):
    with st.spinner("Collecting sources..." if not skip_discovery else "Loading predefined..."):
        from data.sources import PREDEFINED_SOURCES
        if skip_discovery:
            sources = {"predefined": list(PREDEFINED_SOURCES), "dynamic": [], "all": list(PREDEFINED_SOURCES)}
        else:
            sources = collect_all_urls()

    col1, col2, col3 = st.columns(3)
    col1.metric("Predefined", len(sources["predefined"]))
    col2.metric("Dynamic (discovered)", len(sources["dynamic"]))
    col3.metric("Total", len(sources["all"]))

    with st.expander(f"Predefined ({len(sources['predefined'])})"):
        for url in sources["predefined"]:
            st.code(url, language=None)

    if sources["dynamic"]:
        with st.expander(f"Dynamic ({len(sources['dynamic'])})"):
            for url in sources["dynamic"]:
                st.code(url, language=None)

st.divider()

run = st.button("Run Full Pipeline", type="primary")

if run:
    progress_bar = st.progress(0, text="Starting...")
    results_container = st.container()

    def on_progress(index, total, url, origin, result):
        pct = (index + 1) / total
        progress_bar.progress(pct, text=f"{index + 1}/{total}: {url[:60]}...")

        with results_container:
            tier = result.get("tier", "")
            score = result.get("score", "")
            error = result.get("error", "")
            tag = ":globe_with_meridians:" if origin == "dynamic" else ":pushpin:"

            if error:
                st.markdown(f":x: {tag} **{url[:60]}** — _{error[:80]}_")
            elif tier == "gold":
                st.markdown(f":trophy: {tag} **{score}/100** [GOLD] — {url[:60]}")
            elif tier == "review":
                st.markdown(f":warning: {tag} **{score}/100** [REVIEW] — {url[:60]}")
            elif tier == "drop":
                st.markdown(f":wastebasket: {tag} **{score}/100** [DROPPED] — {url[:60]}")

    with st.spinner("Running pipeline..."):
        output = run_pipeline_all(on_progress=on_progress, skip_discovery=skip_discovery)

    progress_bar.progress(1.0, text="Done!")

    # Summary
    st.divider()
    st.subheader("Summary")

    src = output["sources"]
    summary = output["summary"]

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Sources**")
        c1, c2, c3 = st.columns(3)
        c1.metric(":pushpin: Predefined", src["predefined"])
        c2.metric(":globe_with_meridians: Dynamic", src["dynamic"])
        c3.metric("Total", src["total"])

    with col_b:
        st.markdown("**Results**")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Processed", summary["completed"])
        c2.metric(":trophy: Gold", summary["gold"])
        c3.metric(":warning: Review", summary["review"])
        c4.metric(":wastebasket: Dropped", summary["dropped"])
        c5.metric(":x: Errors", summary["errors"])

    errors = [r for r in output["results"] if r.get("error")]
    if errors:
        with st.expander(f"Errors ({len(errors)})"):
            for r in errors:
                st.markdown(f"- `{r['url'][:60]}` — {r['error']}")
