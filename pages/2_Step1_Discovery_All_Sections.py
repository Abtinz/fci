"""Streamlit page for running discovery across all five scorecard sections."""

from __future__ import annotations

import json

import streamlit as st

from ui.discovery import DEFAULT_SECTION_INITIATIVES, run_discovery_batch


st.set_page_config(page_title="Step 1 · Discovery (All Sections)", page_icon="V1M", layout="wide")

st.title("Step 1 · Discovery (All Sections)")
st.caption(
    "Run the discovery node once for each live BestWR scorecard section using representative initiatives."
)

st.info(
    "Live BestWR site checked: https://bestwr.org/ . "
    "The five sections shown there are Housing, Transportation, Healthcare, "
    "Employment & Jobs, and placemaking & livability."
)

st.subheader("Batch Scope")
st.dataframe(DEFAULT_SECTION_INITIATIVES, width="stretch", hide_index=True)

run_batch = st.button("Run Discovery For All Sections", type="primary", width="stretch")

if run_batch:
    with st.spinner("Running discovery across all five sections..."):
        try:
            results = run_discovery_batch()
        except Exception as exc:
            st.error(str(exc))
        else:
            total_sources = sum(len(item.get("sources", [])) for item in results)
            st.success(
                f"Discovery batch finished for {len(results)} sections. "
                f"Total sources found: {total_sources}."
            )

            for result in results:
                initiative = result["initiative"]
                sources = result.get("sources", [])
                label = f"{initiative['category']} | {initiative['name']}"
                with st.expander(label, expanded=True):
                    if not sources:
                        st.warning("No sources returned for this section run.")
                    else:
                        for index, source in enumerate(sources, start=1):
                            st.markdown(f"**Source {index}**")
                            st.json(source)
                    st.markdown("**Full state**")
                    st.code(json.dumps(result, indent=2, default=str), language="json")
