"""Streamlit page: Vision One Million Scorecard Dashboard."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agents.report import generate_report, STATUS_LABELS
from storage.source_store import mongo_configured

st.set_page_config(page_title="Vision One Million Dashboard", page_icon="V1M", layout="wide")

# ── Custom CSS for radar.cloudflare.com style ────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f172a; }
    .main .block-container { max-width: 1200px; padding-top: 2rem; }

    h1, h2, h3, h4, p, span, label, .stMarkdown {
        color: #e2e8f0 !important;
    }

    .score-ring {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 120px;
        height: 120px;
        border-radius: 50%;
        font-size: 2.5rem;
        font-weight: 800;
        color: white;
    }

    .cat-card {
        background: #1e293b;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #334155;
        margin-bottom: 1rem;
    }

    .init-row {
        background: #1e293b;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
        display: inline-block;
    }

    .metric-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #94a3b8;
    }

    .source-count {
        font-size: 0.8rem;
        color: #64748b;
    }

    .stat-card {
        background: #1e293b;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        border: 1px solid #334155;
    }

    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        color: #f8fafc;
    }

    .stat-label {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0;">
        Vision One Million Scorecard
    </h1>
    <p style="color: #94a3b8 !important; font-size: 1.1rem;">
        Waterloo Region Community Progress Dashboard
    </p>
</div>
""", unsafe_allow_html=True)

if not mongo_configured():
    st.warning("MongoDB not configured. Dashboard requires validated data in MongoDB.")
    st.info("Run the Pipeline Runner (page 16) first to populate data.")
    st.stop()

# ── Generate report ──────────────────────────────────────────────────────────
with st.spinner("Generating scorecard report..."):
    try:
        report = generate_report()
    except Exception as exc:
        st.error(f"Report generation failed: {exc}")
        st.stop()

overall = report["overall_score"]
total = report["total_initiatives"]
assessed = report["total_assessed"]
status_counts = report["status_counts"]

# ── Overall score ────────────────────────────────────────────────────────────
def _score_color(score: int) -> str:
    if score >= 70:
        return "#22c55e"
    if score >= 40:
        return "#f59e0b"
    return "#ef4444"

col_score, col_stats = st.columns([1, 3])

with col_score:
    color = _score_color(overall)
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem;">
        <div class="score-ring" style="background: conic-gradient({color} {overall * 3.6}deg, #334155 0deg); margin: 0 auto;">
            <div style="width: 90px; height: 90px; border-radius: 50%; background: #0f172a; display: flex; align-items: center; justify-content: center;">
                {overall}
            </div>
        </div>
        <p style="margin-top: 0.5rem; color: #94a3b8 !important;">Overall Score</p>
    </div>
    """, unsafe_allow_html=True)

with col_stats:
    cols = st.columns(5)
    stat_items = [
        (str(total), "Initiatives"),
        (str(assessed), "Assessed"),
        (str(status_counts.get("ACHIEVED", 0)), "Achieved"),
        (str(status_counts.get("ON_TRACK", 0) + status_counts.get("IN_PROGRESS", 0)), "In Progress"),
        (str(status_counts.get("NEEDS_ATTENTION", 0)), "Needs Attention"),
    ]
    for col, (num, label) in zip(cols, stat_items):
        col.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{num}</div>
            <div class="stat-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Category breakdown ───────────────────────────────────────────────────────
st.markdown("## Categories")

cat_cols = st.columns(len(report["categories"]))
for col, cat in zip(cat_cols, report["categories"]):
    cat_color = _score_color(cat["score"])
    with col:
        st.markdown(f"""
        <div class="cat-card" style="text-align: center;">
            <div style="font-size: 2rem; font-weight: 800; color: {cat_color};">{cat['score']}</div>
            <div style="font-size: 1rem; font-weight: 600; color: #e2e8f0;">{cat['name']}</div>
            <div class="source-count">{cat['assessed_count']}/{cat['initiative_count']} assessed</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Initiative detail ────────────────────────────────────────────────────────
for cat in report["categories"]:
    st.markdown(f"### {cat['name']}")

    for init in cat["initiatives"]:
        status_info = STATUS_LABELS.get(init["status"], STATUS_LABELS["NO_DATA"])
        border_color = status_info["color"]

        st.markdown(f"""
        <div class="init-row" style="border-left-color: {border_color};">
            <div>
                <div style="font-weight: 600; color: #f1f5f9;">{init['name']}</div>
                <div style="font-size: 0.85rem; color: #94a3b8;">
                    {init['metric_label']} &middot; Target: {init['target_value']}
                </div>
            </div>
            <div style="text-align: right;">
                <span class="status-badge" style="background: {border_color};">{init['status_label']}</span>
                <div class="metric-value">{init.get('value', '') or '—'}</div>
                <div class="source-count">{init['source_count']} source(s)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if init.get("reasoning") or init.get("highlights") or init.get("sources"):
            with st.expander(f"Details: {init['name']}", expanded=False):
                if init.get("reasoning"):
                    st.markdown(f"**Assessment:** {init['reasoning']}")

                if init.get("highlights"):
                    st.markdown("**Highlights:**")
                    for h in init["highlights"]:
                        st.markdown(f"- {h}")

                if init.get("sources"):
                    st.markdown(f"**Sources ({len(init['sources'])}):**")
                    for src in init["sources"]:
                        tier_icon = ":trophy:" if src["tier"] == "gold" else ":warning:"
                        st.markdown(
                            f"- {tier_icon} [{src.get('title') or src['url'][:60]}]({src['url']}) "
                            f"— score: {src['score']}, confidence: {src['confidence']}"
                        )
                        if src.get("data_points"):
                            for dp in src["data_points"]:
                                st.markdown(f"  - {dp}")

    st.markdown("<br>", unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem;">
    <p style="color: #64748b !important; font-size: 0.85rem;">
        Vision One Million Scorecard &middot; Waterloo Region &middot;
        Data sourced from government portals, CMHC, Statistics Canada, and municipal reports
    </p>
</div>
""", unsafe_allow_html=True)

# ── Raw data export ──────────────────────────────────────────────────────────
with st.expander("Raw report JSON"):
    st.json(report)
