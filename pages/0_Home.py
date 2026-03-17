import streamlit as st
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import get_connection, get_shipments
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav, _role_normalize

st.set_page_config(page_title="PACE | Overview", page_icon="",
                   layout="wide", initial_sidebar_state="collapsed")
inject_css()

if not check_auth():
    st.warning("Please sign in.")
    st.page_link("app.py", label="Go to Sign In")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

conn = get_connection()
df_all = get_shipments(conn) if conn is not None else pd.DataFrame()
if df_all.empty:
    df_all = generate_mock_shipments(300)
    st.info("Live database unavailable — showing demo data.")
df_all["ship_date_dt"] = pd.to_datetime(df_all["ship_date"])

role = _role_normalize(st.session_state.get("role"))

total_shipments = len(df_all)
month_shipments = len(
    df_all[df_all["ship_date_dt"] >= (df_all["ship_date_dt"].max() - pd.Timedelta(days=30))]
)
avg_risk = float(df_all["risk_score"].mean() * 100) if total_shipments else 0.0
high_risk = int(
    (df_all["risk_tier"].astype(str).str.lower() == "high").sum()
) if total_shipments else 0
exposure = float(df_all["accessorial_charge_usd"].sum()) if total_shipments else 0.0

# ── Hero section ───────────────────────────────────────────────────────────────
hero_left, hero_right = st.columns([1.4, 1.1], gap="large")

with hero_left:
    st.markdown(f"### Welcome back, {username}!")
    st.markdown(
        "<h1 style='font-size:30px;line-height:1.3;margin-bottom:8px;'>"
        "Predict accessorial costs<br>before they hit your margin."
        "</h1>",
        unsafe_allow_html=True,
    )
    st.caption(
        "PACE surfaces high-risk shipments and expected exposure early, so your team can adjust "
        "carriers, routes, and appointments before execution."
    )
    st.markdown("<br>", unsafe_allow_html=True)
    cta1, cta2 = st.columns([1, 1])
    with cta1:
        st.page_link("pages/4_Cost_Estimate.py", label="Risk Estimate")
    with cta2:
        st.page_link("pages/1_Dashboard.py", label="View Dashboards")

with hero_right:
    with st.container(border=True):
        st.markdown("#### This month at a glance")
        st.caption("Key indicators across your network")
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Total shipments", f"{month_shipments:,}")
            st.metric("High-risk pending", f"{high_risk:,}")
        with m2:
            st.metric("Average risk score", f"{avg_risk:.1f}%")
            st.metric("Estimated exposure", f"${exposure:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Feature grid ───────────────────────────────────────────────────────────────
st.markdown("### Everything you need to ship with confidence")
st.caption(
    "Use risk scores, historical insights, and carrier analytics to protect margin across every move."
)

g1, g2, g3 = st.columns(3)
with g1:
    st.markdown("#### Risk prediction")
    st.caption("Instant risk tiers for each shipment, powered by your historical data.")
with g2:
    st.markdown("#### Cost exposure")
    st.caption("Expected accessorial exposure in dollars, surfaced before booking.")
with g3:
    st.markdown("#### Carrier performance")
    st.caption("Lane and carrier views that highlight where risks and costs stack up.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Quick links ────────────────────────────────────────────────────────────────
st.markdown("### Jump into PACE")
ql1, ql2, ql3 = st.columns(3)
with ql1:
    st.page_link("pages/1_Dashboard.py", label="Open Dashboards")
with ql2:
    st.page_link("pages/5_Route_Analysis.py", label="Review Routes")
with ql3:
    st.page_link("pages/7_Accessorial_Tracker.py", label="Track Accessorials")
