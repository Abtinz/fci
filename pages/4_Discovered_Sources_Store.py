"""Streamlit page for browsing discovered sources stored in MongoDB."""

from __future__ import annotations

import streamlit as st

from ui.discovery import get_discovered_sources, get_mongo_connection_status, is_mongo_configured


st.set_page_config(page_title="Discovered Sources Store", page_icon="V1M", layout="wide")

st.title("Discovered Sources Store")
st.caption("Review source candidates persisted from discovery runs.")

if not is_mongo_configured():
    st.error("MongoDB is not configured. Set MONGODB_URI and MONGODB_DB in .env first.")
else:
    ok, message = get_mongo_connection_status()
    if not ok:
        st.error(message)
        st.stop()

    initiative_id = st.text_input("Filter by initiative ID", value="")
    limit = st.slider("Max records", min_value=10, max_value=500, value=100, step=10)

    if st.button("Refresh Stored Sources", type="primary", width="stretch"):
        records = get_discovered_sources(initiative_id=initiative_id or None, limit=limit)
        if not records:
            st.warning("No discovered sources found in MongoDB.")
        else:
            st.success(f"Loaded {len(records)} discovered source record(s).")
            st.dataframe(records, width="stretch", hide_index=True)

            for index, record in enumerate(records, start=1):
                with st.expander(f"Record {index}: {record.get('initiative_id', '')} | {record.get('url', '')}", expanded=False):
                    st.json(record)
