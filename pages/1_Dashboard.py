# File: pages/1_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav, NAVY_900, NAVY_500

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

with st.expander("⚙️ Filters", expanded=False):
    f1, f2, f3 = st.columns(3)
    with f1:
        date_range = st.date_input(
            "Ship Date Range", value=(min_date, max_date),
            min_value=min_date, max_value=max_date, key="dash_date"
        )
    with f2:
        sel_carriers = st.multiselect("Carrier", carriers, default=carriers, key="dash_carriers")
    with f3:
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

# ── Charts row ────────────────────────────────────────────────────────────────
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
                labels=["0–10%","10–20%","20–30%","30–40%","40–50%",
                        "50–60%","60–70%","70–80%","80–90%","90–100%"],
                include_lowest=True,
            )
            bucket_counts = hist_df["bucket"].value_counts().sort_index().reset_index()
            bucket_counts.columns = ["Bracket", "Count"]

            def bucket_color(label):
                pct = int(label.split("–")[0])
                if pct >= 67: return NAVY_900
                if pct >= 34: return "#D97706"
                return "#059669"

            bar_colors = [bucket_color(b) for b in bucket_counts["Bracket"].astype(str)]

            fig = go.Figure(go.Bar(
                x=bucket_counts["Bracket"].astype(str),
                y=bucket_counts["Count"],
                marker_color=bar_colors,
                hovertemplate="<b>%{x}</b><br>%{y} shipments<extra></extra>",
            ))
            fig.update_layout(
                margin=dict(l=0, r=0, t=8, b=0), height=260,
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(tickfont=dict(size=11), gridcolor="#F3F4F6"),
                yaxis=dict(tickfont=dict(size=11), gridcolor="#F3F4F6"),
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

            fig2 = go.Figure(go.Bar(
                x=carrier_risk["risk_pct"],
                y=carrier_risk["carrier"],
                orientation="h",
                marker_color=NAVY_500,
                text=carrier_risk["risk_pct"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Avg Risk: %{x:.1f}%<extra></extra>",
            ))
            fig2.update_layout(
                margin=dict(l=0, r=40, t=8, b=0), height=260,
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(title="Avg Risk Score (%)", range=[0, 100],
                           tickfont=dict(size=11), gridcolor="#F3F4F6"),
                yaxis=dict(tickfont=dict(size=11)),
            )
            st.plotly_chart(fig2, use_container_width=True)
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
