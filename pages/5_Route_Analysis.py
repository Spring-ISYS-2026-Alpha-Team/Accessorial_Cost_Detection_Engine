# File: pages/5_Route_Analysis.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav, NAVY_500, NAVY_900

st.set_page_config(
    page_title="PACE — Route Analysis",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

@st.cache_data
def load_data():
    return generate_mock_shipments(300)

df = load_data()

# ── Inline filters ────────────────────────────────────────────────────────────
with st.expander("⚙️ Filters", expanded=False):
    f1, f2 = st.columns(2)
    with f1:
        min_vol = st.slider("Minimum shipments per lane", 1, 10, 2,
                            help="Filter out low-volume lanes")
    with f2:
        view_by = st.radio("Analyze by",
                           ["Lane (Origin → Dest)", "Origin City", "Destination City"],
                           horizontal=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Route Analysis")
st.caption("Identify your most and least expensive shipping lanes and optimize route selection.")
st.divider()

# ── Build lane metrics ────────────────────────────────────────────────────────
if view_by == "Lane (Origin → Dest)":
    group_col = "lane"
    label     = "Lane"
else:
    group_col = "origin_city" if "Origin" in view_by else "destination_city"
    label     = "Origin" if "Origin" in view_by else "Destination"

lane_metrics = (
    df.groupby(group_col)
    .agg(
        shipments       =("shipment_id",           "count"),
        avg_cost        =("total_cost_usd",         "mean"),
        total_cost      =("total_cost_usd",         "sum"),
        avg_cpm         =("cost_per_mile",          "mean"),
        avg_miles       =("miles",                  "mean"),
        avg_risk        =("risk_score",             "mean"),
        accessorial_cost=("accessorial_charge_usd", "sum"),
        high_risk_count =("risk_tier",
                          lambda x: (x == "High").sum()),
    )
    .reset_index()
    .rename(columns={group_col: label})
)

lane_metrics = lane_metrics[lane_metrics["shipments"] >= min_vol].copy()
lane_metrics["accessorial_rate"] = (
    lane_metrics["accessorial_cost"] / lane_metrics["total_cost"] * 100
).round(1)
lane_metrics["high_risk_pct"] = (
    lane_metrics["high_risk_count"] / lane_metrics["shipments"] * 100
).round(1)

# ── KPI row ───────────────────────────────────────────────────────────────────
total_lanes   = len(lane_metrics)
busiest_lane  = lane_metrics.loc[lane_metrics["shipments"].idxmax(), label] if total_lanes else "—"
cheapest_lane = lane_metrics.loc[lane_metrics["avg_cpm"].idxmin(),  label] if total_lanes else "—"
most_exp_lane = lane_metrics.loc[lane_metrics["avg_cpm"].idxmax(),  label] if total_lanes else "—"

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Active Lanes",    f"{total_lanes}")
with k2:
    st.metric("Busiest Lane",    busiest_lane if len(busiest_lane) < 30 else busiest_lane[:27] + "…")
with k3:
    st.metric("Cheapest $/Mile", cheapest_lane if len(cheapest_lane) < 30 else cheapest_lane[:27] + "…")
with k4:
    st.metric("Most Expensive",  most_exp_lane if len(most_exp_lane) < 30 else most_exp_lane[:27] + "…")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
chart_l, chart_r = st.columns(2, gap="medium")

with chart_l:
    with st.container(border=True):
        st.markdown("#### Most Expensive Lanes")
        st.caption("Top 8 by average cost per mile")
        top_exp = lane_metrics.nlargest(8, "avg_cpm").sort_values("avg_cpm")
        fig = go.Figure(go.Bar(
            x=top_exp["avg_cpm"],
            y=top_exp[label].apply(lambda v: v if len(v) <= 28 else v[:25] + "…"),
            orientation="h",
            marker_color="#DC2626",
            text=top_exp["avg_cpm"].apply(lambda v: f"${v:.2f}/mi"),
            textposition="outside",
        ))
        fig.update_layout(
            margin=dict(l=0, r=80, t=8, b=0), height=300,
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(tickprefix="$", gridcolor="#F3F4F6"),
            yaxis=dict(gridcolor="#F3F4F6"),
        )
        st.plotly_chart(fig, use_container_width=True)

with chart_r:
    with st.container(border=True):
        st.markdown("#### Most Efficient Lanes")
        st.caption("Top 8 by lowest average cost per mile")
        top_cheap = lane_metrics.nsmallest(8, "avg_cpm").sort_values("avg_cpm", ascending=False)
        fig2 = go.Figure(go.Bar(
            x=top_cheap["avg_cpm"],
            y=top_cheap[label].apply(lambda v: v if len(v) <= 28 else v[:25] + "…"),
            orientation="h",
            marker_color="#059669",
            text=top_cheap["avg_cpm"].apply(lambda v: f"${v:.2f}/mi"),
            textposition="outside",
        ))
        fig2.update_layout(
            margin=dict(l=0, r=80, t=8, b=0), height=300,
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(tickprefix="$", gridcolor="#F3F4F6"),
            yaxis=dict(gridcolor="#F3F4F6"),
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Volume vs cost scatter ────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Lane Volume vs Avg Cost")
    st.caption("Identify high-volume expensive lanes — biggest opportunity for savings")
    scatter_fig = px.scatter(
        lane_metrics,
        x="shipments",
        y="avg_cost",
        size="total_cost",
        color="avg_risk",
        hover_name=label,
        color_continuous_scale=["#059669", "#D97706", "#DC2626"],
        labels={
            "shipments": "Shipment Volume",
            "avg_cost":  "Avg Total Cost ($)",
            "avg_risk":  "Avg Risk Score",
            "total_cost":"Total Spend",
        },
        hover_data={"avg_cpm": ":.2f", "accessorial_rate": ":.1f"},
    )
    scatter_fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0), height=320,
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(gridcolor="#F3F4F6"),
        yaxis=dict(gridcolor="#F3F4F6", tickprefix="$"),
    )
    st.plotly_chart(scatter_fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Full lane table ───────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### All Lanes — Full Breakdown")
    display = lane_metrics.copy()
    display["avg_cost"]  = display["avg_cost"].round(2)
    display["avg_cpm"]   = display["avg_cpm"].round(3)
    display["avg_miles"] = display["avg_miles"].round(0).astype(int)
    display["avg_risk"]  = display["avg_risk"].round(3)

    st.dataframe(
        display[[label, "shipments", "avg_cost", "avg_cpm", "avg_miles",
                 "avg_risk", "accessorial_rate", "high_risk_pct", "total_cost"]]
        .rename(columns={
            "shipments":       "Shipments",
            "avg_cost":        "Avg Cost ($)",
            "avg_cpm":         "Avg $/Mile",
            "avg_miles":       "Avg Miles",
            "avg_risk":        "Avg Risk",
            "accessorial_rate":"Accessorial %",
            "high_risk_pct":   "High Risk %",
            "total_cost":      "Total Spend ($)",
        })
        .sort_values("Avg $/Mile", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Avg Risk": st.column_config.ProgressColumn(
                "Avg Risk", format="%.0f%%", min_value=0, max_value=1),
            "Avg Cost ($)":    st.column_config.NumberColumn(format="$%.2f"),
            "Avg $/Mile":      st.column_config.NumberColumn(format="$%.3f"),
            "Total Spend ($)": st.column_config.NumberColumn(format="$%.0f"),
        },
        height=420,
    )
