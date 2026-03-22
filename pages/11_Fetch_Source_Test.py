"""Streamlit page: test fetch_source vs Tavily extract side by side."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from data.sources import PREDEFINED_SOURCES
from tools.crawler import fetch_source, _looks_like_js_rendered
from tools.search import tavily_extract

st.set_page_config(page_title="Fetch Source Test", page_icon="V1M", layout="wide")
st.title("Fetch Source Test")
st.caption("Compare local fetch_source vs Tavily extract side by side.")

url = st.text_input("URL", placeholder="https://example.com/data.pdf")

predef = st.selectbox(
    "Or pick a predefined source",
    options=[""] + PREDEFINED_SOURCES,
    format_func=lambda x: x if x else "— select —",
)
if predef and not url:
    url = predef

col_a, col_b = st.columns(2)
fetch_local = col_a.button("fetch_source (local)", type="primary", disabled=not url)
fetch_tavily = col_b.button("tavily_extract", disabled=not url)
fetch_both = st.button("Run both side by side", disabled=not url)


def _show_local_result(result: str):
    st.metric("Content length", f"{len(result):,} chars")
    if "--- TABLES ---" in result or "--- DATA LINKS ---" in result:
        parts = result.split("\n--- ")
        st.code(parts[0], language=None)
        for part in parts[1:]:
            if part.startswith("TABLES ---"):
                st.markdown("**Tables**")
                st.code(part[len("TABLES ---\n"):], language=None)
            elif part.startswith("DATA LINKS ---"):
                st.markdown("**Data Links**")
                st.markdown(part[len("DATA LINKS ---\n"):])
    else:
        st.code(result, language=None)


def _run_local(url: str) -> str | None:
    try:
        return fetch_source.invoke({"url": url})
    except Exception as exc:
        st.error(f"fetch_source error: {exc}")
        return None


def _run_tavily(url: str) -> str | None:
    try:
        return tavily_extract.invoke({"url": url})
    except Exception as exc:
        st.error(f"tavily_extract error: {exc}")
        return None


if fetch_both and url:
    left, right = st.columns(2)

    with left:
        st.subheader("fetch_source (local)")
        with st.spinner("Fetching locally..."):
            result = _run_local(url)
        if result:
            _show_local_result(result)

    with right:
        st.subheader("tavily_extract")
        with st.spinner("Fetching via Tavily..."):
            result = _run_tavily(url)
        if result:
            st.metric("Content length", f"{len(result):,} chars")
            st.code(result, language=None)

elif fetch_local and url:
    st.subheader("fetch_source (local)")
    with st.spinner("Fetching locally..."):
        result = _run_local(url)
    if result:
        _show_local_result(result)

elif fetch_tavily and url:
    st.subheader("tavily_extract")
    with st.spinner("Fetching via Tavily..."):
        result = _run_tavily(url)
    if result:
        st.metric("Content length", f"{len(result):,} chars")
        st.code(result, language=None)
