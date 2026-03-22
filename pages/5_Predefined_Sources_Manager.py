"""Streamlit page for human-in-the-loop predefined source management."""

from __future__ import annotations

import streamlit as st

from ui.discovery import (
    DEFAULT_SECTION_INITIATIVES,
    get_human_predefined_sources,
    is_mongo_configured,
    save_human_predefined_source,
)


st.set_page_config(page_title="Predefined Sources Manager", page_icon="V1M", layout="wide")

st.title("Predefined Sources Manager")
st.caption("Add human-reviewed predefined sources that discovery can use before Tavily search.")

if not is_mongo_configured():
    st.error("MongoDB is not configured. Set MONGODB_URI and MONGODB_DB in .env first.")
else:
    preset_options = {f"{item['initiative_id']} | {item['name']}": item for item in DEFAULT_SECTION_INITIATIVES}
    preset_label = st.selectbox("Start from a known initiative", options=["Custom"] + list(preset_options.keys()))
    preset = preset_options.get(preset_label)

    left, right = st.columns([1, 1])

    with left:
        initiative_id = st.text_input("Initiative ID", value=(preset or {}).get("initiative_id", ""))
        category = st.text_input("Category", value=(preset or {}).get("category", ""))
        name = st.text_input("Initiative Name", value=(preset or {}).get("name", ""))
        metric_label = st.text_input("Metric", value=(preset or {}).get("metric_label", ""))
        target_value = st.text_input("Target", value=(preset or {}).get("target_value", ""))

    with right:
        url = st.text_input("Source URL", value="")
        source_type = st.selectbox("Source Type", options=["html", "csv", "xlsx", "pdf", "api"], index=0)
        description = st.text_area("Description", value="", height=120)
        notes = st.text_area("Human Notes", value="", height=120)

    if st.button("Save Human Predefined Source", type="primary", use_container_width=True):
        try:
            saved = save_human_predefined_source(
                initiative_id=initiative_id.strip(),
                category=category.strip(),
                name=name.strip(),
                metric_label=metric_label.strip(),
                target_value=target_value.strip(),
                url=url.strip(),
                source_type=source_type,
                description=description.strip(),
                notes=notes.strip(),
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success("Saved predefined source to MongoDB.")
            st.json(saved)

    st.subheader("Saved Human Predefined Sources")
    filter_id = st.text_input("Filter saved sources by initiative ID", value="", key="predefined_filter")
    if st.button("Refresh Predefined Sources", use_container_width=True):
        records = get_human_predefined_sources(filter_id or None)
        if not records:
            st.warning("No human predefined sources found in MongoDB.")
        else:
            st.dataframe(records, use_container_width=True, hide_index=True)
