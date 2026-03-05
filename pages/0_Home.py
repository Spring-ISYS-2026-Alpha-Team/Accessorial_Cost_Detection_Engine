# File: pages/0_Home.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav, NAVY_500, NAVY_900, NAVY_100

st.set_page_config(page_title="PACE — Home", page_icon="🏠",
                   layout="wide", initial_sidebar_state="collapsed")
inject_css()

if not check_auth():
    st.warning("Please sign in.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

@st.cache_data
def load_data():
    return generate_mock_shipments(300)

df_all = load_data()
df_all["ship_date_dt"] = pd.to_datetime(df_all["ship_date"])

# ── Inline date filter ────────────────────────────────────────────────────────
min_d = df_all["ship_date_dt"].min().date()
max_d = df_all["ship_date_dt"].max().date()

with st.expander("⚙️ Filters", expanded=False):
    f1, f2 = st.columns(2)
    with f1:
        date_range = st.date_input("Ship Date Range", value=(min_d, max_d),
                                   min_value=min_d, max_value=max_d, key="home_date")
    with f2:
        st.markdown("")  # spacer

df = df_all.copy()
if len(date_range) == 2:
    df = df[(df["ship_date_dt"] >= pd.Timestamp(date_range[0])) &
            (df["ship_date_dt"] <= pd.Timestamp(date_range[1]))]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Operations Overview")
st.caption("High-level freight performance metrics across all active shipments")
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_shipments   = len(df)
total_revenue     = df["base_freight_usd"].sum()
total_accessorial = df["accessorial_charge_usd"].sum()
total_costs       = df["total_cost_usd"].sum()
avg_cpm           = df["cost_per_mile"].mean()
accessorial_rate  = (len(df[df["accessorial_charge_usd"] > 0]) / total_shipments * 100) if total_shipments else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: st.metric("Total Shipments",   f"{total_shipments:,}")
with k2: st.metric("Total Revenue",     f"${total_revenue:,.0f}")
with k3: st.metric("Total Costs",       f"${total_costs:,.0f}")
with k4: st.metric("Accessorial Costs", f"${total_accessorial:,.0f}")
with k5: st.metric("Avg Cost / Mile",   f"${avg_cpm:.2f}")
with k6: st.metric("Accessorial Rate",  f"{accessorial_rate:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# ── Shipments over time + Revenue vs Cost ─────────────────────────────────────
df["week"] = df["ship_date_dt"].dt.to_period("W").dt.start_time
weekly = (
    df.groupby("week")
    .agg(shipments=("shipment_id", "count"),
         revenue=("base_freight_usd", "sum"),
         total_cost=("total_cost_usd", "sum"))
    .reset_index()
)

col_l, col_r = st.columns(2, gap="medium")

with col_l:
    with st.container(border=True):
        st.markdown("#### Shipments Over Time")
        st.caption("Weekly shipment volume")
        fig = go.Figure(go.Scatter(
            x=weekly["week"], y=weekly["shipments"],
            mode="lines", fill="tozeroy",
            line=dict(color=NAVY_900, width=2),
            fillcolor=NAVY_100,
        ))
        fig.update_layout(margin=dict(l=0,r=0,t=8,b=0), height=260,
                          plot_bgcolor="white", paper_bgcolor="white",
                          xaxis=dict(gridcolor="#F3F4F6"),
                          yaxis=dict(gridcolor="#F3F4F6"))
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    with st.container(border=True):
        st.markdown("#### Revenue vs Total Cost")
        st.caption("Weekly — base revenue vs cost including accessorials")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=weekly["week"], y=weekly["revenue"],
                                  name="Revenue", mode="lines",
                                  line=dict(color=NAVY_500, width=2)))
        fig2.add_trace(go.Scatter(x=weekly["week"], y=weekly["total_cost"],
                                  name="Total Cost", mode="lines",
                                  line=dict(color="#DC2626", width=2, dash="dash")))
        fig2.update_layout(margin=dict(l=0,r=0,t=8,b=0), height=260,
                           plot_bgcolor="white", paper_bgcolor="white",
                           legend=dict(orientation="h", y=1.1),
                           xaxis=dict(gridcolor="#F3F4F6"),
                           yaxis=dict(gridcolor="#F3F4F6", tickprefix="$"))
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Avg cost per mile by carrier + cost breakdown ─────────────────────────────
col_a, col_b = st.columns(2, gap="medium")

with col_a:
    with st.container(border=True):
        st.markdown("#### Avg Cost per Mile by Carrier")
        st.caption("Lower is more cost-efficient")
        cpm = (df.groupby("carrier")["cost_per_mile"].mean()
               .reset_index().sort_values("cost_per_mile"))
        fig3 = go.Figure(go.Bar(
            x=cpm["cost_per_mile"], y=cpm["carrier"], orientation="h",
            marker_color=NAVY_500,
            text=cpm["cost_per_mile"].apply(lambda v: f"${v:.2f}"),
            textposition="outside",
        ))
        fig3.update_layout(margin=dict(l=0,r=60,t=8,b=0), height=280,
                           plot_bgcolor="white", paper_bgcolor="white",
                           xaxis=dict(tickprefix="$", gridcolor="#F3F4F6"),
                           yaxis=dict(gridcolor="#F3F4F6"))
        st.plotly_chart(fig3, use_container_width=True)

with col_b:
    with st.container(border=True):
        st.markdown("#### Cost Breakdown by Carrier")
        st.caption("Base freight vs accessorial charges per carrier")
        cb = (df.groupby("carrier")
              .agg(base=("base_freight_usd", "sum"),
                   acc=("accessorial_charge_usd", "sum"))
              .reset_index().sort_values("base", ascending=False))
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name="Base Freight", x=cb["carrier"],
                              y=cb["base"], marker_color=NAVY_500))
        fig4.add_trace(go.Bar(name="Accessorial", x=cb["carrier"],
                              y=cb["acc"], marker_color="#DC2626"))
        fig4.update_layout(barmode="stack", margin=dict(l=0,r=0,t=8,b=0),
                           height=280, plot_bgcolor="white", paper_bgcolor="white",
                           legend=dict(orientation="h", y=1.1),
                           xaxis=dict(gridcolor="#F3F4F6"),
                           yaxis=dict(gridcolor="#F3F4F6", tickprefix="$"))
        st.plotly_chart(fig4, use_container_width=True)
