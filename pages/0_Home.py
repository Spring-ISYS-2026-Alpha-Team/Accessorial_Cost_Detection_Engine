import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav, NAVY_100, NAVY_500, NAVY_900

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PACE — Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()

# ── Extra page styling for website feel ───────────────────────────────────────
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1280px;
    }

    .hero-wrap {
        background:
            linear-gradient(135deg, rgba(10, 27, 58, 0.96), rgba(24, 56, 107, 0.92));
        border-radius: 24px;
        padding: 52px 44px;
        color: white;
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
        margin-bottom: 22px;
    }

    .hero-badge {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 999px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 16px;
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        line-height: 1.05;
        margin-bottom: 12px;
        letter-spacing: -0.03em;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        line-height: 1.7;
        color: rgba(255,255,255,0.85);
        max-width: 760px;
        margin-bottom: 12px;
    }

    .hero-stat {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 18px;
        padding: 18px 20px;
        margin-top: 10px;
    }

    .hero-stat-label {
        font-size: 12px;
        color: rgba(255,255,255,0.72);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 8px;
    }

    .hero-stat-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: white;
    }

    .section-title {
        font-size: 2rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.35rem;
        letter-spacing: -0.02em;
    }

    .section-subtitle {
        font-size: 0.98rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }

    .feature-card {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 20px;
        padding: 24px 22px;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        min-height: 210px;
    }

    .feature-icon {
        font-size: 1.6rem;
        margin-bottom: 10px;
    }

    .feature-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 8px;
    }

    .feature-text {
        font-size: 0.95rem;
        color: #64748B;
        line-height: 1.65;
    }

    .step-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E5E7EB;
        border-radius: 18px;
        padding: 22px 20px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
        min-height: 160px;
    }

    .step-number {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #0F2E59;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        margin-bottom: 14px;
    }

    .step-title {
        font-size: 1rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 8px;
    }

    .step-text {
        font-size: 0.94rem;
        color: #64748B;
        line-height: 1.6;
    }

    .preview-shell {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 24px;
        padding: 22px;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
        margin-top: 12px;
    }

    .preview-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 18px;
    }

    .preview-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0F172A;
    }

    .preview-subtitle {
        font-size: 0.92rem;
        color: #64748B;
        margin-top: 4px;
    }

    .mini-note {
        font-size: 0.9rem;
        color: #64748B;
    }

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #E5E7EB;
        padding: 16px 18px;
        border-radius: 18px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
    }

    [data-testid="stMetricLabel"] {
        font-weight: 700 !important;
    }

    .cta-note {
        margin-top: 12px;
        color: rgba(255,255,255,0.72);
        font-size: 0.92rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Auth guard ────────────────────────────────────────────────────────────────
if not check_auth():
    st.warning("Please sign in.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

# ── Data source ───────────────────────────────────────────────────────────────
@st.cache_data
def load_mock_data():
    return generate_mock_shipments(300)


# Prefer upload-scored data if available, else upload raw, else mock
if st.session_state.get("upload_scored") is not None:
    df_all = st.session_state["upload_scored"].copy()
    data_source_label = "Uploaded and scored shipment data"
    data_source_icon = "✅"
elif st.session_state.get("upload_df") is not None:
    df_all = st.session_state["upload_df"].copy()
    data_source_label = "Uploaded shipment data (not scored yet)"
    data_source_icon = "📄"
else:
    df_all = load_mock_data()
    data_source_label = "Mock shipment data preview"
    data_source_icon = "🧪"

# Ensure dates
df_all["ship_date_dt"] = pd.to_datetime(df_all.get("ship_date"), errors="coerce")

# Guard columns for preview metrics/charts
for col in [
    "base_freight_usd",
    "accessorial_charge_usd",
    "total_cost_usd",
    "cost_per_mile",
]:
    if col not in df_all.columns:
        df_all[col] = 0

if "shipment_id" not in df_all.columns:
    df_all["shipment_id"] = range(1, len(df_all) + 1)

# ── Top summary stats for hero ────────────────────────────────────────────────
hero_total_shipments = len(df_all)
hero_total_accessorial = float(df_all["accessorial_charge_usd"].sum())
hero_accessorial_rate = (
    len(df_all[df_all["accessorial_charge_usd"] > 0]) / hero_total_shipments * 100
    if hero_total_shipments
    else 0
)
hero_total_revenue = float(df_all["base_freight_usd"].sum())

# ── Hero section ──────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="hero-wrap">
        <div class="hero-badge">AI Logistics Intelligence Platform</div>
        <div class="hero-title">PACE — Predict accessorial costs before they hit your margins.</div>
        <div class="hero-subtitle">
            Transform shipment files into clean, validated data, score accessorial risk with machine learning,
            and explore carrier and route performance through a decision-ready logistics dashboard.
        </div>
        <div class="cta-note">{data_source_icon} Current data source: {data_source_label}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

cta1, cta2, cta3 = st.columns([1.2, 1.2, 2.6])
with cta1:
    st.page_link("pages/2_Upload.py", label="📁 Upload Shipment Data")
with cta2:
    st.page_link("pages/1_Dashboard.py", label="📊 Open Dashboard")
with cta3:
    st.markdown(
        '<div class="mini-note">Use the upload flow to parse CSV, Excel, PDF, and image files before validation and scoring.</div>',
        unsafe_allow_html=True,
    )

s1, s2, s3 = st.columns(3)
with s1:
    st.markdown(
        f"""
        <div class="hero-stat">
            <div class="hero-stat-label">Tracked Shipments</div>
            <div class="hero-stat-value">{hero_total_shipments:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with s2:
    st.markdown(
        f"""
        <div class="hero-stat">
            <div class="hero-stat-label">Accessorial Cost Exposure</div>
            <div class="hero-stat-value">${hero_total_accessorial:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with s3:
    st.markdown(
        f"""
        <div class="hero-stat">
            <div class="hero-stat-label">Accessorial Incidence Rate</div>
            <div class="hero-stat-value">{hero_accessorial_rate:.1f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Features section ──────────────────────────────────────────────────────────
st.markdown('<div class="section-title">What the platform does</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle">PACE is designed as a logistics intelligence product — not just a reporting dashboard.</div>',
    unsafe_allow_html=True,
)

f1, f2, f3 = st.columns(3, gap="large")

with f1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📥</div>
            <div class="feature-title">Upload & normalize shipment data</div>
            <div class="feature-text">
                Accept CSV, Excel, PDF, and image files, then standardize different column formats into a consistent schema for downstream analysis.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with f2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <div class="feature-title">Predict accessorial risk</div>
            <div class="feature-text">
                Score shipments using machine learning so teams can identify high-risk loads before detention, lumper, or layover costs impact profitability.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with f3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <div class="feature-title">Analyze operations & carrier performance</div>
            <div class="feature-text">
                Explore freight trends, carrier efficiency, and accessorial exposure through KPI cards, cost visuals, and route-level performance views.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── How it works ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">How it works</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle">A simple workflow designed to feel like a real logistics product experience.</div>',
    unsafe_allow_html=True,
)

w1, w2, w3, w4 = st.columns(4, gap="medium")

steps = [
    ("1", "Upload files", "Import shipment data from structured or semi-structured sources through the upload pipeline."),
    ("2", "Normalize & validate", "Clean fields, standardize column names, and verify that data is usable for analytics and scoring."),
    ("3", "Score risk", "Generate accessorial risk outputs and surface cost exposure before shipment execution."),
    ("4", "Review insights", "Explore charts, KPIs, and carrier comparisons to support operational and pricing decisions."),
]

for col, (num, title, text) in zip([w1, w2, w3, w4], steps):
    with col:
        st.markdown(
            f"""
            <div class="step-card">
                <div class="step-number">{num}</div>
                <div class="step-title">{title}</div>
                <div class="step-text">{text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Preview filters/data shell ────────────────────────────────────────────────
st.markdown('<div class="section-title">Live operations preview</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle">A quick look at the current data flowing through the system.</div>',
    unsafe_allow_html=True,
)

# Defaults for date range
valid_dates = df_all["ship_date_dt"].dropna()
min_d = valid_dates.min().date() if not valid_dates.empty else None
max_d = valid_dates.max().date() if not valid_dates.empty else None

carriers = ["All"]
if "carrier" in df_all.columns:
    carriers += sorted([c for c in df_all["carrier"].dropna().unique().tolist()])

facilities = ["All"]
if "facility" in df_all.columns:
    facilities += sorted([f for f in df_all["facility"].dropna().unique().tolist()])

tiers = ["All"]
if "risk_tier" in df_all.columns:
    tiers += [t for t in ["Low", "Medium", "High"] if t in set(df_all["risk_tier"].dropna().unique())]

with st.expander("⚙️ Preview Filters", expanded=False):
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        if min_d and max_d:
            date_range = st.date_input(
                "Ship Date Range",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d,
                key="home_date",
            )
        else:
            date_range = None
            st.caption("No valid ship_date values")

    with f2:
        carrier_sel = st.selectbox("Carrier", carriers, index=0, key="home_carrier")

    with f3:
        facility_sel = st.selectbox("Facility", facilities, index=0, key="home_facility")

    with f4:
        tier_sel = st.selectbox("Risk Tier", tiers, index=0, key="home_tier")

# Apply filters
df = df_all.copy()

if date_range and len(date_range) == 2 and "ship_date_dt" in df.columns:
    start_dt = pd.Timestamp(date_range[0])
    end_dt = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    df = df[
        (df["ship_date_dt"].notna())
        & (df["ship_date_dt"] >= start_dt)
        & (df["ship_date_dt"] <= end_dt)
    ]

if carrier_sel != "All" and "carrier" in df.columns:
    df = df[df["carrier"] == carrier_sel]

if facility_sel != "All" and "facility" in df.columns:
    df = df[df["facility"] == facility_sel]

if tier_sel != "All" and "risk_tier" in df.columns:
    df = df[df["risk_tier"] == tier_sel]

st.markdown(
    f'<div class="mini-note">Showing {len(df):,} of {len(df_all):,} shipments after filters.</div>',
    unsafe_allow_html=True,
)

# Guard filtered df columns too
for col in [
    "base_freight_usd",
    "accessorial_charge_usd",
    "total_cost_usd",
    "cost_per_mile",
]:
    if col not in df.columns:
        df[col] = 0

# ── KPI preview ───────────────────────────────────────────────────────────────
total_shipments = len(df)
total_revenue = df["base_freight_usd"].sum()
total_accessorial = df["accessorial_charge_usd"].sum()
total_costs = df["total_cost_usd"].sum()
avg_cpm = df["cost_per_mile"].mean() if total_shipments else 0
accessorial_rate = (
    len(df[df["accessorial_charge_usd"] > 0]) / total_shipments * 100
    if total_shipments
    else 0
)

with st.container():
    st.markdown('<div class="preview-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="preview-header">
            <div>
                <div class="preview-title">Analytics snapshot</div>
                <div class="preview-subtitle">A dashboard preview that makes the homepage feel like a real product, not a static presentation.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        st.metric("Total Shipments", f"{total_shipments:,}")
    with k2:
        st.metric("Total Revenue", f"${total_revenue:,.0f}")
    with k3:
        st.metric("Total Costs", f"${total_costs:,.0f}")
    with k4:
        st.metric("Accessorial Costs", f"${total_accessorial:,.0f}")
    with k5:
        st.metric("Avg Cost / Mile", f"${avg_cpm:.2f}")
    with k6:
        st.metric("Accessorial Rate", f"{accessorial_rate:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    if df["ship_date_dt"].notna().any():
        df["week"] = df["ship_date_dt"].dt.to_period("W").dt.start_time

        weekly = (
            df.groupby("week")
            .agg(
                shipments=("shipment_id", "count"),
                revenue=("base_freight_usd", "sum"),
                total_cost=("total_cost_usd", "sum"),
            )
            .reset_index()
        )

        col_l, col_r = st.columns(2, gap="medium")

        with col_l:
            with st.container(border=True):
                st.markdown("#### Shipments Over Time")
                st.caption("Weekly shipment volume")

                fig = go.Figure(
                    go.Scatter(
                        x=weekly["week"],
                        y=weekly["shipments"],
                        mode="lines",
                        fill="tozeroy",
                        line=dict(color=NAVY_900, width=2),
                        fillcolor=NAVY_100,
                    )
                )
                fig.update_layout(
                    margin=dict(l=0, r=0, t=8, b=0),
                    height=260,
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    xaxis=dict(gridcolor="#F3F4F6"),
                    yaxis=dict(gridcolor="#F3F4F6"),
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_r:
            with st.container(border=True):
                st.markdown("#### Revenue vs Total Cost")
                st.caption("Weekly — base revenue vs cost including accessorials")

                fig2 = go.Figure()
                fig2.add_trace(
                    go.Scatter(
                        x=weekly["week"],
                        y=weekly["revenue"],
                        name="Revenue",
                        mode="lines",
                        line=dict(color=NAVY_500, width=2),
                    )
                )
                fig2.add_trace(
                    go.Scatter(
                        x=weekly["week"],
                        y=weekly["total_cost"],
                        name="Total Cost",
                        mode="lines",
                        line=dict(color="#DC2626", width=2, dash="dash"),
                    )
                )
                fig2.update_layout(
                    margin=dict(l=0, r=0, t=8, b=0),
                    height=260,
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    legend=dict(orientation="h", y=1.1),
                    xaxis=dict(gridcolor="#F3F4F6"),
                    yaxis=dict(gridcolor="#F3F4F6", tickprefix="$"),
                )
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("No valid ship_date values available for time-series charts.")

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        with st.container(border=True):
            st.markdown("#### Avg Cost per Mile by Carrier")
            st.caption("Lower is more cost-efficient")

            if "carrier" in df.columns and len(df) > 0:
                cpm = (
                    df.groupby("carrier")["cost_per_mile"]
                    .mean()
                    .reset_index()
                    .sort_values("cost_per_mile")
                )

                fig3 = go.Figure(
                    go.Bar(
                        x=cpm["cost_per_mile"],
                        y=cpm["carrier"],
                        orientation="h",
                        marker_color=NAVY_500,
                        text=cpm["cost_per_mile"].apply(lambda v: f"${v:.2f}"),
                        textposition="outside",
                    )
                )
                fig3.update_layout(
                    margin=dict(l=0, r=60, t=8, b=0),
                    height=280,
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    xaxis=dict(tickprefix="$", gridcolor="#F3F4F6"),
                    yaxis=dict(gridcolor="#F3F4F6"),
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Carrier / cost_per_mile data not available.")

    with col_b:
        with st.container(border=True):
            st.markdown("#### Cost Breakdown by Carrier")
            st.caption("Base freight vs accessorial charges per carrier")

            if "carrier" in df.columns and len(df) > 0:
                cb = (
                    df.groupby("carrier")
                    .agg(
                        base=("base_freight_usd", "sum"),
                        acc=("accessorial_charge_usd", "sum"),
                    )
                    .reset_index()
                    .sort_values("base", ascending=False)
                )

                fig4 = go.Figure()
                fig4.add_trace(
                    go.Bar(
                        name="Base Freight",
                        x=cb["carrier"],
                        y=cb["base"],
                        marker_color=NAVY_500,
                    )
                )
                fig4.add_trace(
                    go.Bar(
                        name="Accessorial",
                        x=cb["carrier"],
                        y=cb["acc"],
                        marker_color="#DC2626",
                    )
                )
                fig4.update_layout(
                    barmode="stack",
                    margin=dict(l=0, r=0, t=8, b=0),
                    height=280,
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    legend=dict(orientation="h", y=1.1),
                    xaxis=dict(gridcolor="#F3F4F6"),
                    yaxis=dict(gridcolor="#F3F4F6", tickprefix="$"),
                )
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Carrier revenue/cost data not available.")

    st.markdown('</div>', unsafe_allow_html=True)