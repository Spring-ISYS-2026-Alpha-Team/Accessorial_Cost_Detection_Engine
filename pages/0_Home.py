# File: pages/0_Home.py



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
    st.success(
    f"End-to-end pipeline active ✅  (Scored rows: {len(df_all):,})",
    icon="✅"
)
    st.info("Showing uploaded + scored data from Upload page.", icon="📄")

elif st.session_state.get("upload_df") is not None:

    df_all = st.session_state["upload_df"].copy()

    st.info("Showing uploaded data (not scored yet).", icon="📄")

else:

    df_all = load_mock_data()

    st.info("Showing mock shipment data (Azure DB not enabled yet).", icon="🧪")



# Ensure dates

df_all["ship_date_dt"] = pd.to_datetime(df_all.get("ship_date"), errors="coerce")



# ── Filters ───────────────────────────────────────────────────────────────────

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

    # keep standard order if present

    tiers += [t for t in ["Low", "Medium", "High"] if t in set(df_all["risk_tier"].dropna().unique())]



with st.expander("⚙️ Filters", expanded=False):

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



# Date filter

if date_range and len(date_range) == 2 and "ship_date_dt" in df.columns:

    start_dt = pd.Timestamp(date_range[0])

    end_dt = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    df = df[(df["ship_date_dt"].notna()) & (df["ship_date_dt"] >= start_dt) & (df["ship_date_dt"] <= end_dt)]



# Carrier

if carrier_sel != "All" and "carrier" in df.columns:

    df = df[df["carrier"] == carrier_sel]



# Facility

if facility_sel != "All" and "facility" in df.columns:

    df = df[df["facility"] == facility_sel]



# Risk tier

if tier_sel != "All" and "risk_tier" in df.columns:

    df = df[df["risk_tier"] == tier_sel]



st.caption(f"Showing {len(df):,} of {len(df_all):,} shipments after filters.")

st.divider()



# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("## Operations Overview")

st.caption("High-level freight performance metrics across all active shipments")



# ── KPI Cards ─────────────────────────────────────────────────────────────────

total_shipments = len(df)



# Guard columns (in case upload_df doesn't have them all)

for col in ["base_freight_usd", "accessorial_charge_usd", "total_cost_usd", "cost_per_mile"]:

    if col not in df.columns:

        df[col] = 0



total_revenue = df["base_freight_usd"].sum()

total_accessorial = df["accessorial_charge_usd"].sum()

total_costs = df["total_cost_usd"].sum()

avg_cpm = df["cost_per_mile"].mean() if total_shipments else 0

accessorial_rate = (len(df[df["accessorial_charge_usd"] > 0]) / total_shipments * 100) if total_shipments else 0



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



# ── Shipments over time + Revenue vs Cost ─────────────────────────────────────

# If ship_date_dt is missing/invalid, skip time charts gracefully

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



# ── Avg cost per mile by carrier + cost breakdown ─────────────────────────────

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

                .agg(base=("base_freight_usd", "sum"), acc=("accessorial_charge_usd", "sum"))

                .reset_index()

                .sort_values("base", ascending=False)

            )



            fig4 = go.Figure()

            fig4.add_trace(go.Bar(name="Base Freight", x=cb["carrier"], y=cb["base"], marker_color=NAVY_500))

            fig4.add_trace(go.Bar(name="Accessorial", x=cb["carrier"], y=cb["acc"], marker_color="#DC2626"))

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