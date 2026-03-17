# File: pages/loading.py
"""
Loading screen — shown after login, pre-warms all data caches before
redirecting to the destination page stored in session state.
"""
import time
import base64
import os
import pandas as pd
import streamlit as st
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.styling import _role_normalize

st.set_page_config(
    page_title="PACE | Loading",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Redirect if not authenticated
if not check_auth():
    st.switch_page("app.py")
    st.stop()

dest = st.session_state.get("post_load_dest", "pages/0_Home.py")

# If already loaded this session, skip straight to destination
if st.session_state.get("_data_preloaded"):
    st.switch_page(dest)
    st.stop()

# ── Loading page CSS (aligned with global styling) ────────────────────────────
st.markdown(
    """
    <style>
    #loading-logo img {
        width: 180px;
        filter: none;
    }
    [data-testid="stProgressBar"] > div > div {
        background: rgba(255,255,255,0.6) !important;
        border-radius: 2px !important;
        box-shadow: none !important;
    }
    [data-testid="stProgressBar"] > div {
        background: rgba(255,255,255,0.06) !important;
        border-radius: 2px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Logo ───────────────────────────────────────────────────────────────────────
_logo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")
if os.path.exists(_logo):
    with open(_logo, "rb") as f:
        _lb64 = base64.b64encode(f.read()).decode()
    st.markdown(
        f'<div id="loading-logo" style="text-align:center;padding:52px 0 28px;">'
        f'<img src="data:image/png;base64,{_lb64}" />'
        f'</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<div style='text-align:center;padding:60px 0 28px;'>"
        "<div style='font-size:38px;color:#f0f0ee;letter-spacing:0.08em;text-transform:uppercase;'>PACE</div>"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    "<p style='text-align:center;color:rgba(240,240,238,0.45);font-size:13px;margin:-12px 0 28px;'>"
    "Preparing your workspace…</p>",
    unsafe_allow_html=True,
)

# ── Progress bar + status ──────────────────────────────────────────────────────
progress_bar = st.progress(0)
status_slot  = st.empty()


def _step(msg: str, pct: int):
    progress_bar.progress(pct)
    status_slot.markdown(
        f"<p style='text-align:center;color:#E2E8F0;font-size:13px;margin:6px 0;'>{msg}…</p>",
        unsafe_allow_html=True,
    )


# ── Pre-warm all caches ────────────────────────────────────────────────────────
try:
    from utils.database import (
        get_connection, verify_pace_user,
        get_shipments, get_accessorial_charges,
        get_carriers, get_facilities, get_shipments_with_charges,
    )
    from utils.mock_data import generate_mock_shipments
    from utils.cost_model import get_cost_model
    from utils.risk_model import get_risk_model

    _step("Connecting to database", 5)
    conn = get_connection()

    # ── Verify non-fallback users against the DB ───────────────────────────────
    if st.session_state.get("role") == "pending":
        _u = st.session_state.get("username", "")
        _p = st.session_state.pop("_pending_password", "")
        verified_role = verify_pace_user(conn, _u, _p) if conn is not None else None
        if verified_role is None:
            _err = "Invalid credentials or database unavailable."
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state["_login_error"] = _err
            st.switch_page("app.py")
            st.stop()
        st.session_state["role"] = _role_normalize(verified_role)
        dest = "pages/8_Admin.py" if st.session_state["role"] == "admin" else "pages/0_Home.py"
        st.session_state["post_load_dest"] = dest

    _step("Loading shipment records", 20)
    df = get_shipments(conn) if conn is not None else pd.DataFrame()
    if df.empty:
        df = generate_mock_shipments(1000)

    _step("Loading accessorial data", 42)
    get_accessorial_charges(conn)
    get_shipments_with_charges(conn)

    _step("Loading carrier & facility data", 58)
    get_carriers(conn)
    get_facilities(conn)

    _step("Training ML cost model", 68)
    get_cost_model(len(df), df)

    _step("Training risk model", 82)
    get_risk_model(len(df), df)

    _step("Preparing dashboards", 90)
    _df = df.copy()
    _df["ship_date_dt"] = pd.to_datetime(_df["ship_date"])
    _df["week"] = _df["ship_date_dt"].dt.to_period("W").dt.start_time
    st.session_state["_preload_df"] = _df
    st.session_state["_preload_weekly"] = (
        _df.groupby("week")
           .agg(shipments=("shipment_id", "count"),
                revenue=("base_freight_usd", "sum"),
                total_cost=("total_cost_usd", "sum"))
           .reset_index()
    )
    st.session_state["_preload_carrier_cpm"] = (
        _df.groupby("carrier")["cost_per_mile"].mean()
           .reset_index().sort_values("cost_per_mile")
    )

    progress_bar.progress(100)
    status_slot.markdown(
        "<p style='text-align:center;color:#34D399;font-size:14px;font-weight:600;"
        "margin:8px 0;'>✓ &nbsp;Everything ready</p>",
        unsafe_allow_html=True,
    )
    time.sleep(0.15)

except Exception as e:
    progress_bar.progress(100)
    status_slot.markdown(
        f"<p style='text-align:center;color:#FCD34D;font-size:13px;margin:6px 0;'>"
        f"⚠ Loaded with warnings — {e}</p>",
        unsafe_allow_html=True,
    )
    time.sleep(0.3)

st.session_state["_data_preloaded"] = True
st.switch_page(dest)
