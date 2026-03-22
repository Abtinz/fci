"""Streamlit page: nurture raw extracted content into clean structured data."""

from __future__ import annotations

import json

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from data.sources import PREDEFINED_SOURCES
from tools.crawler import fetch_source
from agents.nurture import nurture_content

st.set_page_config(page_title="Content Nurture", page_icon="V1M", layout="wide")
st.title("Content Nurture")
st.caption("Fetch a source, then clean and structure the content via LLM.")

url = st.text_input("URL", placeholder="https://example.com/report.pdf")

predef = st.selectbox(
    "Or pick a predefined source",
    options=[""] + PREDEFINED_SOURCES,
    format_func=lambda x: x if x else "— select —",
)
if predef and not url:
    url = predef

run = st.button("Fetch & Nurture", type="primary", disabled=not url)

if run and url:
    # Step 1: Fetch
    with st.spinner("Fetching source..."):
        try:
            raw = fetch_source.invoke({"url": url})
        except Exception as exc:
            st.error(f"Fetch failed: {exc}")
            st.stop()

    # Step 2: Nurture
    with st.spinner("Nurturing content..."):
        try:
            nurtured = nurture_content(url, raw)
        except Exception as exc:
            st.error(f"Nurture failed: {exc}")
            st.stop()

    # Display
    left, right = st.columns(2)

    with left:
        st.subheader("Raw Input")
        st.metric("Raw length", f"{len(raw):,} chars")
        st.code(raw[:5000], language=None)
        if len(raw) > 5000:
            with st.expander(f"Full raw content ({len(raw):,} chars)"):
                st.code(raw, language=None)

    with right:
        st.subheader("Nurtured Output")

        if nurtured.get("title"):
            st.markdown(f"**{nurtured['title']}**")

        if nurtured.get("summary"):
            st.info(nurtured["summary"])

        if nurtured.get("data_points"):
            st.markdown("**Data Points**")
            for dp in nurtured["data_points"]:
                date_str = f" ({dp['date']})" if dp.get("date") else ""
                st.markdown(f"- **{dp.get('label', '')}**: {dp.get('value', '')}{date_str}")

        if nurtured.get("tables"):
            st.markdown("**Tables**")
            for tbl in nurtured["tables"]:
                st.markdown(f"_{tbl.get('name', 'Table')}_")
                headers = tbl.get("headers", [])
                rows = tbl.get("rows", [])
                if headers and rows:
                    import pandas as pd
                    df = pd.DataFrame(rows, columns=headers[:len(rows[0])] if headers else None)
                    st.dataframe(df, use_container_width=True)

        if nurtured.get("data_links"):
            st.markdown("**Data Links**")
            for link in nurtured["data_links"]:
                st.markdown(f"- [{link.get('label', link.get('url', ''))}]({link.get('url', '')})")

        if nurtured.get("raw_clean_text"):
            with st.expander("Clean text"):
                st.code(nurtured["raw_clean_text"][:5000], language=None)

    st.divider()
    st.subheader("Full JSON Output")
    st.markdown(f"`{url}`")
    st.json(nurtured)
