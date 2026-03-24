"""Streamlit page: Vision One Million Scorecard Dashboard."""

from __future__ import annotations

import json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agents.report import generate_report, STATUS_LABELS
from storage.source_store import mongo_configured

st.set_page_config(page_title="Vision One Million", page_icon="V1M", layout="wide")

# ── Design system from system-design.html ────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
    :root {
        --bg: #FAFAF8;
        --surface: #FFFFFF;
        --border: #E2E0DB;
        --text: #1A1918;
        --muted: #8A877F;
        --green: #1B7A3D;
        --green-bg: #E8F5ED;
        --green-border: #C4E4CE;
        --red: #B83A2A;
        --red-bg: #FCEEED;
        --red-border: #EACBC6;
        --amber: #9B7A1C;
        --amber-bg: #FBF6E8;
        --amber-border: #E8DDB8;
        --blue: #2563A8;
        --blue-bg: #EBF1FA;
        --blue-border: #C0D5ED;
        --teal: #0E7490;
        --teal-bg: #E8F6F8;
    }

    .stApp {
        background: var(--bg) !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    .stApp [data-testid="stHeader"] { background: transparent !important; }
    .stApp [data-testid="stSidebar"] { display: none; }

    /* Reset Streamlit defaults */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp p, .stApp span, .stApp div, .stApp label {
        font-family: 'DM Sans', sans-serif !important;
        color: var(--text) !important;
    }

    .stApp .stMarkdown code {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* ── HERO ── */
    .hero {
        text-align: center;
        padding: 48px 20px 40px;
    }
    .hero-badge {
        display: inline-block;
        font-size: 0.62rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.4px;
        color: var(--blue);
        background: var(--blue-bg);
        border: 1px solid var(--blue-border);
        padding: 4px 14px;
        border-radius: 100px;
        margin-bottom: 16px;
    }
    .hero h1 {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: var(--text) !important;
        margin-bottom: 6px !important;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        font-size: 0.88rem;
        color: var(--muted) !important;
    }

    /* ── SCORE RING ── */
    .score-section {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 48px;
        padding: 20px 0 40px;
        max-width: 900px;
        margin: 0 auto;
    }
    .score-ring-wrap {
        text-align: center;
        flex-shrink: 0;
    }
    .score-ring-outer {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px;
        position: relative;
    }
    .score-ring-inner {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: var(--bg);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    }
    .score-ring-num {
        font-size: 2.8rem;
        font-weight: 800;
        line-height: 1;
    }
    .score-ring-label {
        font-size: 0.68rem;
        color: var(--muted) !important;
        margin-top: 2px;
    }

    /* ── STAT CARDS ── */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        flex: 1;
    }
    .stat-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 16px 12px;
        text-align: center;
    }
    .stat-num {
        font-size: 1.6rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 4px;
    }
    .stat-label {
        font-size: 0.68rem;
        color: var(--muted) !important;
    }

    /* ── CATEGORY CARDS ── */
    .cats-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        max-width: 1100px;
        margin: 0 auto 40px;
    }
    .cat-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        cursor: default;
    }
    .cat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }
    .cat-score {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 6px;
    }
    .cat-name {
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .cat-assessed {
        font-size: 0.66rem;
        color: var(--muted) !important;
    }
    .cat-bar {
        height: 4px;
        border-radius: 2px;
        background: var(--border);
        margin-top: 12px;
        overflow: hidden;
    }
    .cat-bar-fill {
        height: 100%;
        border-radius: 2px;
        transition: width 0.5s ease;
    }

    /* ── SECTION TITLE ── */
    .section-title {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.4px;
        color: var(--muted) !important;
        text-align: center;
        margin-bottom: 20px;
    }

    /* ── INITIATIVE TABLE ── */
    .init-table {
        width: 100%;
        border-collapse: collapse;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 12px;
    }
    .init-table th {
        text-align: left;
        font-size: 0.62rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: var(--muted);
        padding: 12px 16px;
        border-bottom: 1px solid var(--border);
        background: var(--bg);
    }
    .init-table td {
        padding: 12px 16px;
        font-size: 0.78rem;
        border-bottom: 1px solid var(--bg);
        vertical-align: middle;
    }
    .init-table tr:last-child td { border-bottom: none; }
    .init-table tr:hover td { background: var(--bg); }

    .init-name { font-weight: 600; }
    .init-metric {
        font-size: 0.7rem;
        color: var(--muted) !important;
    }
    .init-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.76rem;
        font-weight: 500;
    }
    .init-sources {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.66rem;
        color: var(--muted) !important;
        background: var(--bg);
        padding: 2px 8px;
        border-radius: 4px;
    }

    /* ── STATUS BADGES ── */
    .status-badge {
        display: inline-block;
        font-size: 0.6rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        padding: 3px 10px;
        border-radius: 100px;
    }
    .status-achieved { background: var(--green-bg); color: var(--green) !important; }
    .status-on-track { background: var(--blue-bg); color: var(--blue) !important; }
    .status-in-progress { background: var(--amber-bg); color: var(--amber) !important; }
    .status-needs-attention { background: var(--red-bg); color: var(--red) !important; }
    .status-no-data { background: var(--bg); color: var(--muted) !important; border: 1px solid var(--border); }

    /* ── CATEGORY LABEL ── */
    .cat-label {
        font-size: 0.6rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        display: inline-block;
    }
    .cat-housing { background: var(--blue-bg); color: var(--blue) !important; }
    .cat-transportation { background: var(--green-bg); color: var(--green) !important; }
    .cat-healthcare { background: var(--red-bg); color: var(--red) !important; }
    .cat-employment { background: var(--amber-bg); color: var(--amber) !important; }
    .cat-livability { background: var(--teal-bg); color: var(--teal) !important; }

    /* ── DETAIL CARD ── */
    .detail-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        border-left: 4px solid;
    }
    .detail-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
    }
    .detail-title {
        font-size: 0.9rem;
        font-weight: 700;
    }
    .detail-reasoning {
        font-size: 0.78rem;
        color: var(--muted) !important;
        line-height: 1.5;
        margin-bottom: 10px;
    }
    .detail-highlight {
        font-size: 0.74rem;
        padding: 4px 0;
        border-bottom: 1px solid var(--bg);
    }
    .detail-highlight:last-child { border-bottom: none; }

    .source-pill {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid var(--border);
        background: var(--bg);
        margin: 2px;
        color: var(--muted) !important;
    }
    .source-pill.gold { border-color: var(--green-border); background: var(--green-bg); color: var(--green) !important; }
    .source-pill.review { border-color: var(--amber-border); background: var(--amber-bg); color: var(--amber) !important; }

    /* ── FOOTER ── */
    .dash-footer {
        text-align: center;
        padding: 40px 20px;
        font-size: 0.72rem;
        color: var(--muted) !important;
        border-top: 1px solid var(--border);
        margin-top: 40px;
    }

    @media (max-width: 768px) {
        .stats-grid { grid-template-columns: repeat(3, 1fr); }
        .cats-grid { grid-template-columns: repeat(2, 1fr); }
        .score-section { flex-direction: column; }
    }
</style>
""", unsafe_allow_html=True)


def _score_color(score: int) -> str:
    if score >= 70: return "var(--green)"
    if score >= 40: return "var(--amber)"
    return "var(--red)"


def _status_class(status: str) -> str:
    return {
        "ACHIEVED": "status-achieved",
        "ON_TRACK": "status-on-track",
        "IN_PROGRESS": "status-in-progress",
        "NEEDS_ATTENTION": "status-needs-attention",
        "NO_DATA": "status-no-data",
    }.get(status, "status-no-data")


def _cat_class(cat_id: str) -> str:
    return f"cat-{cat_id}"


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">Community Scorecard</div>
    <h1>Vision One Million</h1>
    <div class="hero-sub">Waterloo Region Progress Dashboard</div>
</div>
""", unsafe_allow_html=True)

if not mongo_configured():
    st.warning("MongoDB not configured. Run the Pipeline first to populate data.")
    st.stop()

with st.spinner("Generating scorecard..."):
    try:
        report = generate_report()
    except Exception as exc:
        st.error(f"Report generation failed: {exc}")
        st.stop()

overall = report["overall_score"]
total = report["total_initiatives"]
assessed = report["total_assessed"]
sc = report["status_counts"]

# ── Overall Score + Stats ────────────────────────────────────────────────────
color = _score_color(overall)
achieved = sc.get("ACHIEVED", 0)
on_track = sc.get("ON_TRACK", 0)
in_progress = sc.get("IN_PROGRESS", 0)
needs_att = sc.get("NEEDS_ATTENTION", 0)
no_data = sc.get("NO_DATA", 0)

st.markdown(f"""
<div class="score-section">
    <div class="score-ring-wrap">
        <div class="score-ring-outer" style="background: conic-gradient({color} {overall * 3.6}deg, var(--border) 0deg);">
            <div class="score-ring-inner">
                <div class="score-ring-num" style="color: {color};">{overall}</div>
                <div class="score-ring-label">Overall Score</div>
            </div>
        </div>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-num" style="color: var(--text);">{total}</div>
            <div class="stat-label">Initiatives</div>
        </div>
        <div class="stat-card">
            <div class="stat-num" style="color: var(--green);">{achieved}</div>
            <div class="stat-label">Achieved</div>
        </div>
        <div class="stat-card">
            <div class="stat-num" style="color: var(--blue);">{on_track + in_progress}</div>
            <div class="stat-label">In Progress</div>
        </div>
        <div class="stat-card">
            <div class="stat-num" style="color: var(--red);">{needs_att}</div>
            <div class="stat-label">Needs Attention</div>
        </div>
        <div class="stat-card">
            <div class="stat-num" style="color: var(--muted);">{no_data}</div>
            <div class="stat-label">No Data</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Category Cards ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Categories</div>', unsafe_allow_html=True)

cat_cards_html = '<div class="cats-grid">'
for cat in report["categories"]:
    c = _score_color(cat["score"])
    pct = cat["score"]
    cat_cards_html += f"""
    <div class="cat-card">
        <div class="cat-score" style="color: {c};">{cat['score']}</div>
        <div class="cat-name">{cat['name']}</div>
        <div class="cat-assessed">{cat['assessed_count']}/{cat['initiative_count']} assessed</div>
        <div class="cat-bar"><div class="cat-bar-fill" style="width: {pct}%; background: {c};"></div></div>
    </div>
    """
cat_cards_html += '</div>'
st.markdown(cat_cards_html, unsafe_allow_html=True)

# ── Initiative Table ─────────────────────────────────────────────────────────
st.markdown('<div class="section-title">All Initiatives</div>', unsafe_allow_html=True)

table_html = """
<table class="init-table">
    <thead>
        <tr>
            <th>Category</th>
            <th>Initiative</th>
            <th>Current Value</th>
            <th>Target</th>
            <th>Status</th>
            <th>Sources</th>
        </tr>
    </thead>
    <tbody>
"""

for init in report["initiatives"]:
    cat_id = init["category"].lower().replace(" & ", "-").replace(" ", "-").split("-")[0]
    sc_cls = _status_class(init["status"])
    label = STATUS_LABELS.get(init["status"], STATUS_LABELS["NO_DATA"])["label"]
    value = init.get("value") or "—"

    table_html += f"""
    <tr>
        <td><span class="cat-label cat-{cat_id}">{init['category']}</span></td>
        <td>
            <div class="init-name">{init['name']}</div>
            <div class="init-metric">{init['metric_label']}</div>
        </td>
        <td><span class="init-value">{value}</span></td>
        <td><span class="init-metric">{init['target_value']}</span></td>
        <td><span class="status-badge {sc_cls}">{label}</span></td>
        <td><span class="init-sources">{init['source_count']} source(s)</span></td>
    </tr>
    """

table_html += "</tbody></table>"
st.markdown(table_html, unsafe_allow_html=True)

# ── Detailed Breakdown by Category ───────────────────────────────────────────
st.markdown('<div class="section-title" style="margin-top: 40px;">Detailed Breakdown</div>', unsafe_allow_html=True)

for cat in report["categories"]:
    cat_id = cat["id"]
    st.markdown(f"### {cat['name']}")

    for init in cat["initiatives"]:
        status_info = STATUS_LABELS.get(init["status"], STATUS_LABELS["NO_DATA"])
        sc_cls = _status_class(init["status"])
        border_color = status_info["color"]

        # Build source pills
        source_pills = ""
        for src in init.get("sources", []):
            tier_cls = "gold" if src.get("tier") == "gold" else "review"
            title = src.get("title") or src.get("url", "")[:40]
            source_pills += f'<span class="source-pill {tier_cls}" title="{src.get("url", "")}">{title[:35]}</span>'

        # Build highlights
        highlights_html = ""
        for h in init.get("highlights", []):
            highlights_html += f'<div class="detail-highlight">&#8226; {h}</div>'

        detail_html = f"""
        <div class="detail-card" style="border-left-color: {border_color};">
            <div class="detail-header">
                <div>
                    <div class="detail-title">{init['name']}</div>
                    <div class="init-metric">{init['metric_label']} &middot; Target: {init['target_value']}</div>
                </div>
                <div style="text-align: right;">
                    <span class="status-badge {sc_cls}">{status_info['label']}</span>
                    <div class="init-value" style="margin-top: 4px;">{init.get('value') or '—'}</div>
                </div>
            </div>
        """

        if init.get("reasoning"):
            detail_html += f'<div class="detail-reasoning">{init["reasoning"]}</div>'

        if highlights_html:
            detail_html += highlights_html

        if source_pills:
            detail_html += f'<div style="margin-top: 10px;">{source_pills}</div>'

        detail_html += "</div>"
        st.markdown(detail_html, unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-footer">
    Vision One Million Scorecard &middot; Waterloo Region &middot;
    Kitchener &middot; Cambridge &middot; Waterloo<br>
    Data sourced from government portals, CMHC, Statistics Canada, and municipal reports
</div>
""", unsafe_allow_html=True)

# ── Raw export ───────────────────────────────────────────────────────────────
with st.expander("Export raw report JSON"):
    st.json(report)
