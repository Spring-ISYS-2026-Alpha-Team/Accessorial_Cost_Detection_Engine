# File: pages/1_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav, NAVY_900, NAVY_500, NAVY_100

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PACE — Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

# ── Auth guard ────────────────────────────────────────────────────────────────
if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

# ── Dark theme color palette ──────────────────────────────────────────────────
DARK_BG = "#0B1120"          # deep navy-black background
DARK_CARD = "#111827"        # slightly lighter card background
DARK_SURFACE = "#1F2937"     # borders, hover states
GRID_COLOR = "#1F2937"       # subtle grid lines
TEXT_PRIMARY = "#F9FAFB"     # bright white text
TEXT_SECONDARY = "#9CA3AF"   # muted gray text
TEXT_MUTED = "#6B7280"       # very muted text

ACCENT_BLUE = "#3B82F6"      # primary accent
ACCENT_CYAN = "#06B6D4"      # secondary accent
ACCENT_GREEN = "#10B981"     # low risk / positive
ACCENT_AMBER = "#F59E0B"     # medium risk / warning
ACCENT_RED = "#EF4444"       # high risk / danger
ACCENT_PURPLE = "#8B5CF6"    # additional accent

# ── Shared Plotly layout ─────────────────────────────────────────────────────
DARK_LAYOUT = dict(
    plot_bgcolor=DARK_CARD,
    paper_bgcolor=DARK_CARD,
    font=dict(color=TEXT_PRIMARY, size=12),
    xaxis=dict(
        gridcolor=DARK_SURFACE,
        tickfont=dict(color=TEXT_SECONDARY, size=11),
        title_font=dict(color=TEXT_SECONDARY, size=12),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor=DARK_SURFACE,
        tickfont=dict(color=TEXT_SECONDARY, size=11),
        title_font=dict(color=TEXT_SECONDARY, size=12),
        zeroline=False,
    ),
)

# ── Dark theme CSS override ───────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Dark background for the entire page ─────────────────── */
.stApp {{
    background-color: {DARK_BG} !important;
}}

/* ── All text defaults to light ──────────────────────────── */
.stApp, .stApp p, .stApp span, .stApp label,
.stApp .stMarkdown, .stApp [data-testid="stText"] {{
    color: {TEXT_PRIMARY} !important;
}}

/* ── Headings ────────────────────────────────────────────── */
.stApp h1, .stApp h2 {{
    color: {TEXT_PRIMARY} !important;
}}
.stApp h3, .stApp h4 {{
    color: {TEXT_PRIMARY} !important;
}}

/* ── Captions / small text ───────────────────────────────── */
.stApp .stCaption, .stApp small,
.stApp [data-testid="stCaptionContainer"] {{
    color: {TEXT_SECONDARY} !important;
}}

/* ── Metric cards ────────────────────────────────────────── */
[data-testid="stMetric"] {{
    background: {DARK_CARD} !important;
    border: 1px solid {DARK_SURFACE} !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
}}
[data-testid="stMetricLabel"] > div {{
    color: {TEXT_SECONDARY} !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
}}
[data-testid="stMetricValue"] > div {{
    color: {TEXT_PRIMARY} !important;
    font-size: 26px !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricDelta"] > div {{
    font-size: 12px !important;
}}

/* ── Container borders (chart cards) ─────────────────────── */
[data-testid="stVerticalBlock"] > div[data-testid="element-container"]
> div > div > div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {DARK_CARD} !important;
    border: 1px solid {DARK_SURFACE} !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25) !important;
}}

/* ── Bordered containers ─────────────────────────────────── */
div:has(> [data-testid="stVerticalBlockBorderWrapper"]) {{
    border-color: {DARK_SURFACE} !important;
}}

/* ── Expander ────────────────────────────────────────────── */
.streamlit-expanderHeader {{
    background: {DARK_CARD} !important;
    color: {TEXT_PRIMARY} !important;
    border-color: {DARK_SURFACE} !important;
}}
[data-testid="stExpander"] {{
    background: {DARK_CARD} !important;
    border-color: {DARK_SURFACE} !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] details {{
    background: {DARK_CARD} !important;
    border-color: {DARK_SURFACE} !important;
}}
[data-testid="stExpander"] summary {{
    color: {TEXT_PRIMARY} !important;
}}

/* ── Dividers ────────────────────────────────────────────── */
hr {{
    border-color: {DARK_SURFACE} !important;
}}

/* ── Multiselect and date inputs ─────────────────────────── */
[data-testid="stMultiSelect"],
[data-testid="stDateInput"] {{
    color: {TEXT_PRIMARY} !important;
}}
.stMultiSelect > div > div {{
    background: {DARK_SURFACE} !important;
    border-color: {DARK_SURFACE} !important;
    color: {TEXT_PRIMARY} !important;
}}
.stDateInput > div > div > input {{
    background: {DARK_SURFACE} !important;
    color: {TEXT_PRIMARY} !important;
}}

/* ── Search input ────────────────────────────────────────── */
.stTextInput > div > div > input {{
    background: {DARK_SURFACE} !important;
    color: {TEXT_PRIMARY} !important;
    border-color: {DARK_SURFACE} !important;
}}
.stTextInput > div > div > input::placeholder {{
    color: {TEXT_MUTED} !important;
}}

/* ── Dataframe ───────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 1px solid {DARK_SURFACE} !important;
    border-radius: 8px !important;
}}

/* ── Block container padding ─────────────────────────────── */
.block-container {{
    padding-top: 1rem !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Load data (cached) ────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return generate_mock_shipments(300)

df_all = load_data()
df_all["ship_date_dt"] = pd.to_datetime(df_all["ship_date"])

# ── Inline filters ────────────────────────────────────────────────────────────
min_date = df_all["ship_date_dt"].min().date()
max_date = df_all["ship_date_dt"].max().date()
carriers = sorted(df_all["carrier"].unique())
facilities = sorted(df_all["facility"].unique())

with st.expander("⚙️ Filters", expanded=False):
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        date_range = st.date_input(
            "Ship Date Range", value=(min_date, max_date),
            min_value=min_date, max_value=max_date, key="dash_date"
        )
    with f2:
        sel_carriers = st.multiselect("Carrier", carriers, default=carriers, key="dash_carriers")
    with f3:
        sel_facilities = st.multiselect("Facility", facilities, default=facilities, key="dash_facilities")
    with f4:
        sel_tiers = st.multiselect(
            "Risk Tier", ["Low", "Medium", "High"],
            default=["Low", "Medium", "High"], key="dash_tiers"
        )

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_all.copy()
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    df = df[(df["ship_date_dt"] >= start) & (df["ship_date_dt"] <= end)]
if sel_carriers:
    df = df[df["carrier"].isin(sel_carriers)]
if sel_facilities:
    df = df[df["facility"].isin(sel_facilities)]
if sel_tiers:
    df = df[df["risk_tier"].isin(sel_tiers)]

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("## Risk Dashboard")
st.caption(f"Showing {len(df):,} shipments matching current filters")
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
total        = len(df)
avg_risk     = df["risk_score"].mean() * 100 if total else 0
high_risk    = len(df[df["risk_tier"] == "High"])
est_cost     = df["accessorial_charge_usd"].sum()

total_delta     = total - len(df_all)
avg_risk_delta  = (df["risk_score"].mean() - df_all["risk_score"].mean()) * 100 if total else 0
high_risk_delta = high_risk - len(df_all[df_all["risk_tier"] == "High"])
est_cost_delta  = est_cost - df_all["accessorial_charge_usd"].sum()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Shipments",     f"{total:,}",            delta=f"{total_delta:+,} vs all")
with c2:
    st.metric("Avg Risk Score",      f"{avg_risk:.1f}%",      delta=f"{avg_risk_delta:+.1f}%")
with c3:
    st.metric("High-Risk Shipments", f"{high_risk:,}",        delta=f"{high_risk_delta:+,} vs all")
with c4:
    st.metric("Est. Accessorial Cost", f"${est_cost:,.0f}",  delta=f"${est_cost_delta:+,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row 1: Distribution + Carrier Risk ────────────────────────────────
col_left, col_right = st.columns(2, gap="medium")

with col_left:
    with st.container(border=True):
        st.markdown("#### Risk Score Distribution")
        st.caption("Number of shipments by risk score bracket")

        if total > 0:
            hist_df = df.copy()
            hist_df["bucket"] = pd.cut(
                hist_df["risk_score"],
                bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                labels=["0–10%", "10–20%", "20–30%", "30–40%", "40–50%",
                        "50–60%", "60–70%", "70–80%", "80–90%", "90–100%"],
                include_lowest=True,
            )
            bucket_counts = hist_df["bucket"].value_counts().sort_index().reset_index()
            bucket_counts.columns = ["Bracket", "Count"]

            def bucket_color(label):
                pct = int(label.split("–")[0])
                if pct >= 67:
                    return ACCENT_RED
                if pct >= 34:
                    return ACCENT_AMBER
                return ACCENT_GREEN

            bar_colors = [bucket_color(b) for b in bucket_counts["Bracket"].astype(str)]

            fig = go.Figure(go.Bar(
                x=bucket_counts["Bracket"].astype(str),
                y=bucket_counts["Count"],
                marker_color=bar_colors,
                marker_line_width=0,
                text=bucket_counts["Count"],
                textposition="outside",
                textfont=dict(color=TEXT_SECONDARY, size=11),
                hovertemplate="<b>%{x}</b><br>%{y} shipments<extra></extra>",
            ))
            fig.update_layout(
                **DARK_LAYOUT,
                margin=dict(l=0, r=0, t=8, b=0), height=280,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data matches the current filters.")

with col_right:
    with st.container(border=True):
        st.markdown("#### Avg Risk Score by Carrier")
        st.caption("Carriers ranked by average predicted risk")

        if total > 0:
            carrier_risk = (
                df.groupby("carrier")["risk_score"]
                .mean()
                .reset_index()
                .sort_values("risk_score", ascending=True)
            )
            carrier_risk["risk_pct"] = (carrier_risk["risk_score"] * 100).round(1)

            # Gradient from cyan (low risk) to red (high risk)
            def carrier_bar_color(pct):
                if pct >= 67:
                    return ACCENT_RED
                if pct >= 50:
                    return ACCENT_AMBER
                return ACCENT_BLUE

            c_colors = [carrier_bar_color(p) for p in carrier_risk["risk_pct"]]

            fig2 = go.Figure(go.Bar(
                x=carrier_risk["risk_pct"],
                y=carrier_risk["carrier"],
                orientation="h",
                marker_color=c_colors,
                marker_line_width=0,
                text=carrier_risk["risk_pct"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside",
                textfont=dict(color=TEXT_SECONDARY, size=11),
                hovertemplate="<b>%{y}</b><br>Avg Risk: %{x:.1f}%<extra></extra>",
            ))
            fig2.update_layout(
                **DARK_LAYOUT,
                margin=dict(l=0, r=50, t=8, b=0), height=280,
            )
            fig2.update_xaxes(title_text="Avg Risk Score (%)", range=[0, 100])
            fig2.update_yaxes(tickfont=dict(color=TEXT_PRIMARY, size=12))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No data matches the current filters.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row 2 (PB-19): Donut + Facility Risk ──────────────────────────────
chart_a, chart_b = st.columns(2, gap="medium")

with chart_a:
    with st.container(border=True):
        st.markdown("#### Risk Tier Breakdown")
        st.caption("Proportion of shipments in each risk category")

        if total > 0:
            tier_counts = df["risk_tier"].value_counts().reset_index()
            tier_counts.columns = ["Tier", "Count"]

            tier_order = {"Low": 0, "Medium": 1, "High": 2}
            tier_counts["sort"] = tier_counts["Tier"].map(tier_order)
            tier_counts = tier_counts.sort_values("sort").drop(columns="sort")

            tier_colors = {
                "Low": ACCENT_GREEN,
                "Medium": ACCENT_AMBER,
                "High": ACCENT_RED,
            }

            fig_donut = go.Figure(go.Pie(
                labels=tier_counts["Tier"],
                values=tier_counts["Count"],
                hole=0.6,
                marker=dict(
                    colors=[tier_colors[t] for t in tier_counts["Tier"]],
                    line=dict(color=DARK_CARD, width=3),
                ),
                textinfo="label+percent",
                textfont=dict(color=TEXT_PRIMARY, size=13),
                hovertemplate="<b>%{label}</b><br>%{value} shipments<br>%{percent}<extra></extra>",
            ))
            fig_donut.add_annotation(
                text=f"<b>{total:,}</b><br><span style='font-size:11px;color:{TEXT_SECONDARY}'>shipments</span>",
                x=0.5, y=0.5, font_size=20, font_color=TEXT_PRIMARY,
                showarrow=False,
            )
            fig_donut.update_layout(
                margin=dict(l=0, r=0, t=8, b=0), height=320,
                paper_bgcolor=DARK_CARD,
                plot_bgcolor=DARK_CARD,
                font=dict(color=TEXT_PRIMARY),
                showlegend=True,
                legend=dict(
                    orientation="h", y=-0.05, x=0.5, xanchor="center",
                    font=dict(color=TEXT_SECONDARY, size=12),
                ),
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No data matches the current filters.")

with chart_b:
    with st.container(border=True):
        st.markdown("#### Risk by Facility")
        st.caption("Which facilities have the highest average risk scores")

        if total > 0:
            facility_risk = (
                df.groupby("facility")
                .agg(
                    avg_risk=("risk_score", "mean"),
                    count=("shipment_id", "count"),
                    high_count=("risk_tier", lambda x: (x == "High").sum()),
                )
                .reset_index()
                .sort_values("avg_risk", ascending=True)
            )
            facility_risk["risk_pct"] = (facility_risk["avg_risk"] * 100).round(1)
            facility_risk["high_pct"] = (
                facility_risk["high_count"] / facility_risk["count"] * 100
            ).round(1)

            def fac_color(pct):
                if pct >= 60:
                    return ACCENT_RED
                if pct >= 45:
                    return ACCENT_AMBER
                return ACCENT_CYAN

            fac_colors = [fac_color(p) for p in facility_risk["risk_pct"]]

            fig_fac = go.Figure(go.Bar(
                x=facility_risk["risk_pct"],
                y=facility_risk["facility"],
                orientation="h",
                marker_color=fac_colors,
                marker_line_width=0,
                text=facility_risk["risk_pct"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside",
                textfont=dict(color=TEXT_SECONDARY, size=11),
                customdata=facility_risk[["count", "high_pct"]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Avg Risk: %{x:.1f}%<br>"
                    "Shipments: %{customdata[0]}<br>"
                    "High-Risk: %{customdata[1]:.1f}%<extra></extra>"
                ),
            ))
            fig_fac.update_layout(
                **DARK_LAYOUT,
                margin=dict(l=0, r=60, t=8, b=0), height=320,
            )
            fig_fac.update_xaxes(title_text="Avg Risk Score (%)", range=[0, 100])
            fig_fac.update_yaxes(tickfont=dict(color=TEXT_PRIMARY, size=11))
            st.plotly_chart(fig_fac, use_container_width=True)
        else:
            st.info("No data matches the current filters.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Chart C (PB-19): Risk Trend Over Time ─────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Risk Trend Over Time")
    st.caption("Weekly average risk score — see if risk is increasing or decreasing")

    if total > 0:
        trend_df = df.copy()
        trend_df["week"] = trend_df["ship_date_dt"].dt.to_period("W").dt.start_time

        weekly_risk = (
            trend_df.groupby("week")
            .agg(
                avg_risk=("risk_score", "mean"),
                shipments=("shipment_id", "count"),
                high_count=("risk_tier", lambda x: (x == "High").sum()),
            )
            .reset_index()
        )
        weekly_risk["avg_risk_pct"] = (weekly_risk["avg_risk"] * 100).round(1)
        weekly_risk["high_pct"] = (
            weekly_risk["high_count"] / weekly_risk["shipments"] * 100
        ).round(1)

        fig_trend = go.Figure()

        # Gradient fill area
        fig_trend.add_trace(go.Scatter(
            x=weekly_risk["week"],
            y=weekly_risk["avg_risk_pct"],
            mode="lines+markers",
            name="Avg Risk Score",
            line=dict(color=ACCENT_BLUE, width=3),
            marker=dict(color=ACCENT_BLUE, size=7, line=dict(color=DARK_CARD, width=2)),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.12)",
            customdata=weekly_risk[["shipments", "high_pct"]].values,
            hovertemplate=(
                "<b>Week of %{x|%b %d}</b><br>"
                "Avg Risk: %{y:.1f}%<br>"
                "Shipments: %{customdata[0]}<br>"
                "High-Risk: %{customdata[1]:.1f}%<extra></extra>"
            ),
        ))

        # Overall average reference line
        overall_avg = df["risk_score"].mean() * 100
        fig_trend.add_hline(
            y=overall_avg,
            line_dash="dot",
            line_color=TEXT_MUTED,
            line_width=1,
            annotation_text=f"Overall Avg: {overall_avg:.1f}%",
            annotation_position="top right",
            annotation_font_color=TEXT_SECONDARY,
            annotation_font_size=11,
        )

        fig_trend.update_layout(
            **DARK_LAYOUT,
            margin=dict(l=0, r=0, t=8, b=0), height=280,
            showlegend=False,
        )
        fig_trend.update_yaxes(title_text="Avg Risk Score (%)", range=[0, 100])
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No data matches the current filters.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Shipments table ───────────────────────────────────────────────────────────
with st.container(border=True):
    th_col, search_col = st.columns([3, 1])
    with th_col:
        st.markdown("#### Recent Shipments")
    with search_col:
        search = st.text_input("", placeholder="🔍 Search shipment ID…", label_visibility="collapsed")

    table_df = df.copy()
    if search:
        table_df = table_df[table_df["shipment_id"].str.contains(search.upper(), na=False)]

    st.dataframe(
        table_df[[
            "shipment_id", "ship_date", "carrier", "facility",
            "risk_score", "risk_tier", "base_freight_usd", "accessorial_charge_usd",
        ]].rename(columns={
            "shipment_id":            "Shipment ID",
            "ship_date":              "Ship Date",
            "carrier":                "Carrier",
            "facility":               "Facility",
            "risk_score":             "Risk Score",
            "risk_tier":              "Risk Tier",
            "base_freight_usd":       "Base Freight ($)",
            "accessorial_charge_usd": "Est. Accessorial ($)",
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Risk Score": st.column_config.ProgressColumn(
                "Risk Score", format="%.0f%%", min_value=0, max_value=1,
            ),
            "Base Freight ($)":      st.column_config.NumberColumn(format="$%.2f"),
            "Est. Accessorial ($)":  st.column_config.NumberColumn(format="$%.2f"),
        },
        height=400,
    )
    st.caption(f"{len(table_df):,} shipments shown")