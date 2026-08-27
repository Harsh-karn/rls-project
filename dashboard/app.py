"""
RemoteLegalStaff — Ops Intelligence Dashboard (portfolio build)
================================================================
A Streamlit dashboard built for the RLS "AI-Powered Data Analyst" role.

Data source: /database/rls_ops.db (built from fully synthetic data — see
/docs/PROJECT_DOCUMENTATION.md for the full data dictionary and disclaimer).

Run:
    streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import streamlit as st

# ---------------------------------------------------------------------------
# Brand palette
# NOTE: RemoteLegalStaff's public site uses a minimalist black/white wordmark
# (black logo on light backgrounds, white logo on a dark footer) with warm,
# gold-toned accent imagery. Exact brand hex values weren't pulled from a
# design system, so this palette is a professional, closely-matched
# interpretation built around that black/gold/off-white identity — swap the
# constants below for exact hex codes if RLS shares official brand assets.
# ---------------------------------------------------------------------------
INK = "#111111"          # near-black, primary text / wordmark
GOLD = "#C9A54B"          # warm gold accent, used for CTAs/highlights
GOLD_DARK = "#9C7D34"
CREAM = "#F5F3EE"         # soft off-white background
SLATE = "#5B5B5B"         # secondary text / muted elements
GREEN = "#3F7D58"         # positive / healthy
RED = "#B3432B"           # negative / at-risk
NAVY = "#1F2A3C"          # optional deep accent for contrast series

CHART_SEQUENCE = [GOLD, INK, SLATE, GREEN, RED, NAVY, GOLD_DARK]

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "rls_ops.db"

st.set_page_config(
    page_title="RLS Ops Intelligence Dashboard",
    page_icon="⚖️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Global CSS — brand header, KPI cards, fonts
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        .stApp {{ background-color: {CREAM}; }}
        .rls-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.1rem 1.6rem;
            background-color: {INK};
            border-radius: 10px;
            margin-bottom: 1.4rem;
        }}
        .rls-header h1 {{
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin: 0;
        }}
        .rls-header p {{
            color: {GOLD};
            margin: 0;
            font-size: 0.85rem;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }}
        .rls-tag {{
            background-color: {GOLD};
            color: {INK};
            padding: 0.35rem 0.9rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        div[data-testid="stMetric"] {{
            background-color: white;
            border: 1px solid #E7E2D6;
            border-left: 4px solid {GOLD};
            border-radius: 8px;
            padding: 0.9rem 1rem 0.6rem 1rem;
        }}
        div[data-testid="stMetricLabel"] {{ color: {SLATE}; font-weight: 600; }}
        h2, h3 {{ color: {INK}; }}
        .section-note {{ color: {SLATE}; font-size: 0.85rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    clients = pd.read_sql("SELECT * FROM clients", conn)
    candidates = pd.read_sql("SELECT * FROM candidates", conn)
    placements = pd.read_sql("SELECT * FROM placements", conn)
    escalations = pd.read_sql("SELECT * FROM escalations", conn)
    reporting = pd.read_sql("SELECT * FROM reporting_tasks", conn)
    conn.close()

    candidates["application_date"] = pd.to_datetime(candidates["application_date"])
    candidates["stage_date"] = pd.to_datetime(candidates["stage_date"])
    placements["start_date"] = pd.to_datetime(placements["start_date"])
    placements["end_date"] = pd.to_datetime(placements["end_date"], errors="coerce")
    escalations["date_raised"] = pd.to_datetime(escalations["date_raised"])
    escalations["resolution_date"] = pd.to_datetime(escalations["resolution_date"], errors="coerce")
    reporting["due_date"] = pd.to_datetime(reporting["due_date"])

    return clients, candidates, placements, escalations, reporting


clients, candidates, placements, escalations, reporting = load_data()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="rls-header">
        <div>
            <h1>REMOTELEGALSTAFF</h1>
            <p>Ops Intelligence · Weekly Leadership Dashboard</p>
        </div>
        <div class="rls-tag">DATA ANALYST PORTFOLIO PROJECT</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    f"<p class='section-note'>Built on fully synthetic data modeled after RLS's ATS, CRM, "
    f"Monday.com, and Bloom Growth systems. Refresh cadence simulated: weekly. "
    f"See <code>docs/PROJECT_DOCUMENTATION.md</code> for the data dictionary.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")
role_filter = st.sidebar.multiselect(
    "Role", sorted(candidates["role_applied"].unique()), default=[]
)
region_filter = st.sidebar.multiselect(
    "Candidate region", sorted(candidates["region"].unique()), default=[]
)

cand_view = candidates.copy()
if role_filter:
    cand_view = cand_view[cand_view["role_applied"].isin(role_filter)]
if region_filter:
    cand_view = cand_view[cand_view["region"].isin(region_filter)]

plac_view = placements.copy()
if role_filter:
    plac_view = plac_view[plac_view["role"].isin(role_filter)]
if region_filter:
    plac_view = plac_view[plac_view["region"].isin(region_filter)]

esc_view = escalations[escalations["placement_id"].isin(plac_view["placement_id"])]

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<span class='section-note'>Filters apply to the funnel, retention, and "
    "escalation sections below. KPI header row always reflects the full book of business.</span>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# KPI row (mirrors the 4b "weekly leadership summary" SQL query)
# ---------------------------------------------------------------------------
total_placements = len(placements)
active_placements = (placements["status"] == "Active").sum()
retention_rate = round(100 * active_placements / total_placements, 1) if total_placements else 0
open_escalations = (escalations["resolved"] == 0).sum()
offered_or_placed = candidates[candidates["current_stage"].isin(["Offered", "Placed"])]
close_rate = (
    round(100 * (candidates["current_stage"] == "Placed").sum() / len(offered_or_placed), 1)
    if len(offered_or_placed)
    else 0
)
new_applicants_30d = (candidates["application_date"] >= (candidates["application_date"].max() - pd.Timedelta(days=30))).sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Retention rate", f"{retention_rate}%", help="Active placements ÷ all placements ever made")
k2.metric("Close rate", f"{close_rate}%", help="Placed ÷ (Offered + Placed) — offer-stage conversion")
k3.metric("Open escalations", int(open_escalations), help="Unresolved issues logged in Bloom Growth")
k4.metric("Active clients", clients["client_id"].nunique())
k5.metric("New applicants (30d)", int(new_applicants_30d))

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Funnel & Close Rate", "🔁 Retention", "🚩 Escalations", "🧹 Reporting Hygiene"]
)

# ---------------------------------------------------------------------------
# TAB 1 — Funnel & Close Rate
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Candidate funnel")
    stage_order = ["Applied", "Screened", "Interviewed", "Offered", "Placed", "Rejected", "Withdrawn"]
    funnel_counts = cand_view["current_stage"].value_counts().reindex(stage_order).fillna(0)

    core_funnel = funnel_counts[["Applied", "Screened", "Interviewed", "Offered", "Placed"]]
    fig_funnel = go.Figure(
        go.Funnel(
            y=core_funnel.index,
            x=core_funnel.values,
            marker={"color": [INK, SLATE, GOLD_DARK, GOLD, GREEN]},
            textinfo="value+percent initial",
        )
    )
    fig_funnel.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, b=10), height=380
    )
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.plotly_chart(fig_funnel, use_container_width=True)
    with col_b:
        st.markdown("**Outcomes off the core funnel**")
        st.dataframe(
            funnel_counts[["Rejected", "Withdrawn"]].rename("candidates").to_frame(),
            use_container_width=True,
        )
        st.markdown(
            f"<span class='section-note'>Close rate is measured as Placed ÷ "
            f"(Offered + Placed) — the conversion staffing agencies actually manage to, "
            f"since it isolates decisions made once a candidate is offer-ready.</span>",
            unsafe_allow_html=True,
        )

    st.markdown("#### Close rate by role")
    role_stats = (
        cand_view.groupby("role_applied")["current_stage"]
        .apply(lambda s: pd.Series({
            "offered_or_placed": s.isin(["Offered", "Placed"]).sum(),
            "placed": (s == "Placed").sum(),
        }))
        .unstack()
    )
    role_stats["close_rate_pct"] = (
        100 * role_stats["placed"] / role_stats["offered_or_placed"].replace(0, pd.NA)
    ).round(1)
    role_stats = role_stats.dropna(subset=["close_rate_pct"]).sort_values("close_rate_pct", ascending=False)

    fig_role = px.bar(
        role_stats.reset_index(),
        x="close_rate_pct",
        y="role_applied",
        orientation="h",
        color_discrete_sequence=[GOLD],
        text="close_rate_pct",
        labels={"close_rate_pct": "Close rate (%)", "role_applied": ""},
    )
    fig_role.update_traces(texttemplate="%{text}%", textposition="outside", marker_line_color=INK, marker_line_width=0.5)
    fig_role.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, b=10), height=380)
    st.plotly_chart(fig_role, use_container_width=True)

    st.markdown("#### Sourcing channel performance")
    channel_stats = (
        cand_view.groupby("source_channel")
        .agg(total_applicants=("candidate_id", "count"),
             placed=("current_stage", lambda s: (s == "Placed").sum()))
        .reset_index()
    )
    channel_stats["placement_rate_pct"] = (100 * channel_stats["placed"] / channel_stats["total_applicants"]).round(1)
    fig_channel = px.scatter(
        channel_stats,
        x="total_applicants",
        y="placement_rate_pct",
        size="placed",
        color="source_channel",
        color_discrete_sequence=CHART_SEQUENCE,
        text="source_channel",
        labels={"total_applicants": "Total applicants", "placement_rate_pct": "Placement rate (%)"},
    )
    fig_channel.update_traces(textposition="top center")
    fig_channel.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, b=10), height=380, showlegend=False)
    st.plotly_chart(fig_channel, use_container_width=True)
    st.caption("Bubble size = candidates placed. High applicant volume with low placement rate flags a channel worth re-evaluating for spend.")

# ---------------------------------------------------------------------------
# TAB 2 — Retention
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Retention")

    plac_view = plac_view.copy()
    plac_view["start_month"] = plac_view["start_date"].dt.to_period("M").astype(str)
    cohort = (
        plac_view.groupby("start_month")
        .agg(placements_started=("placement_id", "count"),
             still_active=("status", lambda s: (s == "Active").sum()))
        .reset_index()
    )
    cohort["pct_active"] = (100 * cohort["still_active"] / cohort["placements_started"]).round(1)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        fig_cohort = px.bar(
            cohort, x="start_month", y="placements_started",
            color_discrete_sequence=[INK],
            labels={"start_month": "Start month", "placements_started": "Placements started"},
        )
        fig_cohort.add_scatter(
            x=cohort["start_month"], y=cohort["pct_active"], mode="lines+markers",
            name="% still active", yaxis="y2", line=dict(color=GOLD, width=3),
        )
        fig_cohort.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, b=10), height=400,
            yaxis2=dict(overlaying="y", side="right", title="% still active", range=[0, 105]),
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_cohort, use_container_width=True)
    with col_b:
        st.markdown("**Churn reason breakdown**")
        ended = plac_view[plac_view["status"] == "Ended"]
        if len(ended):
            reason_counts = ended["end_reason"].value_counts().reset_index()
            reason_counts.columns = ["end_reason", "count"]
            fig_reason = px.pie(
                reason_counts, names="end_reason", values="count",
                color_discrete_sequence=CHART_SEQUENCE, hole=0.45,
            )
            fig_reason.update_layout(paper_bgcolor="white", margin=dict(t=10, b=10), height=380,
                                      legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_reason, use_container_width=True)
        else:
            st.info("No ended placements in the current filter selection.")

    st.markdown("#### Retention by role and region")
    retention_grid = (
        plac_view.groupby(["role", "region"])
        .agg(total=("placement_id", "count"), active=("status", lambda s: (s == "Active").sum()))
        .reset_index()
    )
    retention_grid = retention_grid[retention_grid["total"] >= 2]
    retention_grid["retention_pct"] = (100 * retention_grid["active"] / retention_grid["total"]).round(1)
    pivot = retention_grid.pivot(index="role", columns="region", values="retention_pct")
    fig_heat = px.imshow(
        pivot,
        text_auto=True,
        color_continuous_scale=[[0, "#F1E4C3"], [0.5, GOLD], [1, GREEN]],
        aspect="auto",
        labels=dict(color="Retention %"),
    )
    fig_heat.update_layout(paper_bgcolor="white", margin=dict(t=10, b=10), height=420)
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("Cells require at least 2 placements in that role × region combination to reduce noise from small samples.")

# ---------------------------------------------------------------------------
# TAB 3 — Escalations
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Escalations")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### By category and severity")
        cat_sev = esc_view.groupby(["category", "severity"]).size().reset_index(name="count")
        fig_cat = px.bar(
            cat_sev, x="category", y="count", color="severity",
            color_discrete_map={"High": RED, "Medium": GOLD, "Low": SLATE},
            barmode="stack",
        )
        fig_cat.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, b=10), height=380,
                               xaxis_title="", legend_title="Severity")
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_b:
        st.markdown("#### Resolution SLA")
        esc_view = esc_view.copy()
        esc_view["days_to_resolve"] = (esc_view["resolution_date"] - esc_view["date_raised"]).dt.days
        sla = (
            esc_view.groupby("severity")
            .agg(total=("escalation_id", "count"),
                 resolved=("resolved", "sum"),
                 avg_days=("days_to_resolve", "mean"))
            .reindex(["High", "Medium", "Low"])
        )
        sla["pct_resolved"] = (100 * sla["resolved"] / sla["total"]).round(1)
        sla["avg_days"] = sla["avg_days"].round(1)
        st.dataframe(
            sla[["total", "resolved", "pct_resolved", "avg_days"]].rename(
                columns={"total": "Raised", "resolved": "Resolved",
                         "pct_resolved": "% Resolved", "avg_days": "Avg days to resolve"}
            ),
            use_container_width=True,
        )
        st.markdown(
            f"<span class='section-note'>High-severity issues should resolve fastest; "
            f"a High-severity average slower than Medium is a process flag worth raising.</span>",
            unsafe_allow_html=True,
        )

    st.markdown("#### Open escalations needing attention")
    open_esc = esc_view[esc_view["resolved"] == 0].merge(
        clients[["client_id", "firm_name"]], on="client_id", how="left"
    )
    open_esc["days_open"] = (pd.Timestamp(candidates["application_date"].max()) - open_esc["date_raised"]).dt.days
    open_esc = open_esc.sort_values(["severity", "days_open"], ascending=[True, False])
    st.dataframe(
        open_esc[["escalation_id", "firm_name", "category", "severity", "date_raised", "days_open"]],
        use_container_width=True, hide_index=True,
    )

# ---------------------------------------------------------------------------
# TAB 4 — Reporting Hygiene (Monday.com board + data QA)
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Reporting cadence & data hygiene")
    st.markdown(
        "<span class='section-note'>Directly reflects the role's success metric: "
        "\"dashboards run clean with zero blanks or broken links at any weekly check.\" "
        "This tab is what a periodic handoff test would check.</span>",
        unsafe_allow_html=True,
    )

    cadence = (
        reporting.groupby("report_name")
        .agg(weeks_tracked=("task_id", "count"),
             weeks_overdue=("status", lambda s: (s == "Overdue").sum()),
             pct_on_time=("on_time", "mean"))
        .reset_index()
    )
    cadence["pct_on_time"] = (100 * cadence["pct_on_time"]).round(1)
    cadence = cadence.sort_values("pct_on_time")

    fig_cadence = px.bar(
        cadence, x="pct_on_time", y="report_name", orientation="h",
        color="pct_on_time", color_continuous_scale=[[0, RED], [0.6, GOLD], [1, GREEN]],
        labels={"pct_on_time": "% delivered on time", "report_name": ""},
        text="pct_on_time",
    )
    fig_cadence.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_cadence.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, b=10), height=380,
                               coloraxis_showscale=False)
    st.plotly_chart(fig_cadence, use_container_width=True)

    st.markdown("#### Automated data-quality checks (run before every dashboard refresh)")
    checks = {
        "Candidates missing a stage date": (candidates["stage_date"].isna()).sum(),
        "Ended placements missing an end date": ((placements["status"] == "Ended") & (placements["end_date"].isna())).sum(),
        "Active placements with an end date set": ((placements["status"] == "Active") & (placements["end_date"].notna())).sum(),
        "Placements ending before they start": ((placements["end_date"].notna()) & (placements["end_date"] < placements["start_date"])).sum(),
        "Duplicate candidate IDs": candidates["candidate_id"].duplicated().sum(),
        "Resolved escalations missing a resolution date": ((escalations["resolved"] == 1) & (escalations["resolution_date"].isna())).sum(),
    }
    check_df = pd.DataFrame(list(checks.items()), columns=["Check", "Issues found"])
    check_df["Status"] = check_df["Issues found"].apply(lambda x: "✅ Pass" if x == 0 else "⚠️ Needs review")
    st.dataframe(check_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(
    "Portfolio project built for the RemoteLegalStaff AI-Powered Data Analyst role · "
    "All data synthetic · See docs/PROJECT_DOCUMENTATION.md for methodology, SQL source, and interview talking points."
)
