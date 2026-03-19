# File: app.py
import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_utils import check_auth

st.set_page_config(
    page_title="PACE",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Fallback credentials (no DB needed) ───────────────────────────────────────
_FALLBACK = {
    "admin": {"password": "admin", "role": "admin"},
    "user":  {"password": "user",  "role": "user"},
}


# ── Login page ─────────────────────────────────────────────────────────────────
def _login_page():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.title("📦 PACE")
        st.caption("Predictive Accessorial Cost Engine")
        st.divider()

        _err = st.session_state.pop("_login_error", None)
        if _err:
            st.error(_err)

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        if submitted:
            if username and password:
                u, p = username.strip(), password
                if u in _FALLBACK and p == _FALLBACK[u]["password"]:
                    role = _FALLBACK[u]["role"]
                else:
                    role = "pending"
                    st.session_state["_pending_password"] = p

                st.session_state["authenticated"] = True
                st.session_state["username"] = u
                st.session_state["role"] = role
                st.session_state["_data_preloaded"] = False
                st.rerun()
            else:
                st.error("Please enter both username and password.")


# ── Pre-warm caches (runs once per session after login) ───────────────────────
def _preload():
    if st.session_state.get("_data_preloaded"):
        return

    with st.spinner("Loading PACE workspace…"):
        try:
            import pandas as pd
            from utils.database import (
                get_connection, verify_pace_user,
                get_shipments, get_accessorial_charges,
                get_carriers, get_facilities, get_shipments_with_charges,
            )
            from utils.mock_data import generate_mock_shipments
            from pipeline.config import is_pace_model_ready

            conn = get_connection()

            # Verify non-fallback users against the DB
            if st.session_state.get("role") == "pending":
                _u = st.session_state.get("username", "")
                _p = st.session_state.pop("_pending_password", "")
                verified_role = verify_pace_user(conn, _u, _p) if conn is not None else None
                if verified_role is None:
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.session_state["_login_error"] = "Invalid credentials or database unavailable."
                    st.rerun()
                st.session_state["role"] = verified_role

            df = get_shipments(conn) if conn is not None else pd.DataFrame()
            if df.empty:
                df = generate_mock_shipments(1000)

            get_accessorial_charges(conn)
            get_shipments_with_charges(conn)
            get_carriers(conn)
            get_facilities(conn)

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

            try:
                from pipeline.inference import get_inference_engine
                if is_pace_model_ready():
                    get_inference_engine()
            except Exception:
                pass

        except Exception:
            pass

    st.session_state["_data_preloaded"] = True


# ── Role-based navigation ──────────────────────────────────────────────────────
if check_auth():
    _preload()

    role = st.session_state.get("role", "user")

    pages = [
        st.Page("pages/0_Home.py",               title="Home",           icon="🏠"),
        st.Page("pages/1_Dashboard.py",           title="Dashboard",      icon="📊"),
        st.Page("pages/2_Upload.py",              title="Upload",         icon="📤"),
        st.Page("pages/4_Cost_Estimate.py",       title="Cost Estimate",  icon="💰"),
        st.Page("pages/6_Carrier_Comparison.py",  title="Carriers",       icon="🚚"),
        st.Page("pages/7_Accessorial_Tracker.py", title="Accessorial",    icon="📋"),
        st.Page("pages/9_Carrier_Lookup.py",      title="Carrier Lookup", icon="🔍"),
        st.Page("pages/chatbot.py",               title="Chatbot",        icon="💬"),
    ]

    if role == "admin":
        pages.append(st.Page("pages/8_Admin.py", title="Admin", icon="🛠️"))

    pg = st.navigation(pages)
    pg.run()

else:
    pg = st.navigation(
        [st.Page(_login_page, title="Sign In", icon="📦")],
        position="hidden",
    )
    pg.run()
