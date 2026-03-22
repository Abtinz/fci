"""Streamlit page: review extraction errors logged for human review."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from storage.source_store import (
    EXTRACTION_ERROR_CATEGORIES,
    get_extraction_error_summary,
    list_extraction_errors,
    mark_error_reviewed,
    mongo_configured,
)

st.set_page_config(page_title="Extraction Errors", page_icon="V1M", layout="wide")
st.title("Extraction Errors")
st.caption("Sources that failed extraction — logged for human review.")

if not mongo_configured():
    st.warning("MongoDB is not configured. Errors are not being persisted.")
    st.stop()

# ── Summary ──────────────────────────────────────────────────────────────────
summary = get_extraction_error_summary()
total_unreviewed = sum(summary.values())

if total_unreviewed == 0:
    st.success("No unreviewed extraction errors.")
else:
    st.error(f"{total_unreviewed} unreviewed error(s)")

cols = st.columns(len(EXTRACTION_ERROR_CATEGORIES))
for i, (cat_id, cat) in enumerate(EXTRACTION_ERROR_CATEGORIES.items()):
    count = summary.get(cat_id, 0)
    cols[i].metric(cat["label"], count)

st.divider()

# ── Filters ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

category_options = ["All"] + [f"{cat['label']} ({cat_id})" for cat_id, cat in EXTRACTION_ERROR_CATEGORIES.items()]
selected_cat = col1.selectbox("Category", category_options)
category_filter = None
if selected_cat != "All":
    category_filter = selected_cat.split("(")[-1].rstrip(")")

review_filter = col2.selectbox("Status", ["Unreviewed", "Reviewed", "All"])
reviewed = None
if review_filter == "Unreviewed":
    reviewed = False
elif review_filter == "Reviewed":
    reviewed = True

initiative_filter = col3.text_input("Initiative ID", "")

# ── Error list ───────────────────────────────────────────────────────────────
errors = list_extraction_errors(
    category=category_filter,
    reviewed=reviewed,
    initiative_id=initiative_filter or None,
)

st.subheader(f"Errors ({len(errors)})")

if not errors:
    st.info("No errors matching filters.")
else:
    for i, err in enumerate(errors):
        status_icon = "white_check_mark" if err.get("reviewed") else "x"
        cat_label = EXTRACTION_ERROR_CATEGORIES.get(err.get("error_category", ""), {}).get("label", err.get("error_category", ""))

        with st.expander(
            f":{status_icon}: **{err.get('error_code', '?')}** — {err.get('url', '')[:80]}",
            expanded=False,
        ):
            col_a, col_b, col_c = st.columns(3)
            col_a.markdown(f"**Category:** {cat_label}")
            col_b.markdown(f"**Code:** `{err.get('error_code', '')}`")
            if err.get("http_status"):
                col_c.markdown(f"**HTTP Status:** {err['http_status']}")

            st.markdown(f"**URL:** `{err.get('url', '')}`")
            st.markdown(f"**Message:** {err.get('error_message', '')}")

            if err.get("initiative_id"):
                st.markdown(f"**Initiative:** `{err['initiative_id']}`")

            if err.get("raw_response_preview"):
                st.code(err["raw_response_preview"], language=None)

            logged = err.get("logged_at", "")
            st.caption(f"Logged: {logged}")

            if err.get("reviewed"):
                st.success(f"Reviewed — Resolution: {err.get('resolution', 'none')}")
            else:
                resolution = st.text_input("Resolution note", key=f"res_{i}", placeholder="e.g. site is down, will retry later")
                if st.button("Mark as reviewed", key=f"review_{i}"):
                    mark_error_reviewed(err["url"], err["error_code"], resolution)
                    st.rerun()
