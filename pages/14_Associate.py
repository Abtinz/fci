"""Streamlit page: fetch, nurture, then associate content with initiatives."""

from __future__ import annotations

import json

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from data.sources import PREDEFINED_SOURCES, SCORECARD_INITIATIVES
from tools.crawler import fetch_source
from agents.nurture import nurture_content
from agents.associate import associate_content

st.set_page_config(page_title="Associate", page_icon="V1M", layout="wide")
st.title("Associate Sources to Initiatives")
st.caption("Fetch → Nurture → Associate content with scorecard initiatives from the knowledge base.")

url = st.text_input("URL", placeholder="https://example.com/report.pdf")

predef = st.selectbox(
    "Or pick a predefined source",
    options=[""] + PREDEFINED_SOURCES,
    format_func=lambda x: x if x else "— select —",
)
if predef and not url:
    url = predef

run = st.button("Fetch → Nurture → Associate", type="primary", disabled=not url)

if run and url:
    # Step 1: Fetch
    with st.spinner("1/3 Fetching source..."):
        try:
            raw = fetch_source.invoke({"url": url})
        except Exception as exc:
            st.error(f"Fetch failed: {exc}")
            st.stop()
    st.success(f"Fetched {len(raw):,} chars")

    # Step 2: Nurture
    with st.spinner("2/3 Nurturing content..."):
        try:
            nurtured = nurture_content(url, raw)
        except Exception as exc:
            st.error(f"Nurture failed: {exc}")
            st.stop()
    st.success(f"Nurtured — {len(nurtured.get('data_points', []))} data points extracted")

    # Step 3: Associate
    with st.spinner("3/3 Associating with initiatives..."):
        try:
            result = associate_content(url, nurtured)
        except Exception as exc:
            st.error(f"Association failed: {exc}")
            st.stop()

    associations = result.get("associations", [])
    st.success(f"Mapped to {len(associations)} initiative(s)")

    # ── Display associations ─────────────────────────────────────────────
    st.subheader("Associations")

    if not associations:
        st.warning("No initiatives matched this source.")
    else:
        for assoc in associations:
            confidence = assoc.get("confidence", "?")
            color = {"high": "green", "medium": "orange", "low": "red"}.get(confidence, "gray")

            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.markdown(f"**{assoc.get('initiative_id', '')}** — {assoc.get('initiative_name', '')}")
                col2.markdown(f"_{assoc.get('category', '')}_  \nMetric: {assoc.get('metric_label', '')}")
                col3.markdown(f"Confidence: :{color}[**{confidence}**]")

                st.markdown(f"**Reasoning:** {assoc.get('reasoning', '')}")

                data_pts = assoc.get("relevant_data_points", [])
                if data_pts:
                    st.markdown("**Relevant data points:**")
                    for dp in data_pts:
                        st.markdown(f"- {dp}")

    # ── Nurtured data ────────────────────────────────────────────────────
    with st.expander("Nurtured data"):
        if nurtured.get("title"):
            st.markdown(f"**{nurtured['title']}**")
        if nurtured.get("summary"):
            st.info(nurtured["summary"])
        if nurtured.get("data_points"):
            for dp in nurtured["data_points"]:
                date_str = f" ({dp['date']})" if dp.get("date") else ""
                st.markdown(f"- **{dp.get('label', '')}**: {dp.get('value', '')}{date_str}")

    # ── Full JSON ────────────────────────────────────────────────────────
    with st.expander("Full JSON output"):
        st.json(result)
