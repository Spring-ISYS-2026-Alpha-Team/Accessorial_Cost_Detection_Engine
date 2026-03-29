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
    # Sidebar hosts st.navigation(); collapsed hides all page links until user finds the toggle
    initial_sidebar_state="expanded",
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


# ── Role-based navigation ──────────────────────────────────────────────────────
if check_auth():
    # Show loading screen first — it pre-warms all caches then reruns here
    if not st.session_state.get("_data_preloaded"):
        pg = st.navigation(
            [st.Page("pages/_loading.py", title="Loading", icon="⏳")],
            position="hidden",
        )
        pg.run()
        st.stop()

    role = st.session_state.get("role", "user")

    pages = [
        st.Page("pages/0_Home.py",               title="Home",           icon="🏠"),
        st.Page("pages/1_Dashboard.py",          title="Dashboard",      icon="📊"),
        st.Page("pages/2_Upload.py",             title="Upload",         icon="📤"),
        st.Page("pages/3_Shipments.py",          title="Shipments",      icon="🚚"),
        st.Page("pages/4_Cost_Estimate.py",      title="Cost Estimate",  icon="💰"),
        st.Page("pages/5_Route_Analysis.py",     title="Routes",         icon="🗺️"),
        st.Page("pages/6_Carrier_Comparison.py", title="Carriers",       icon="🚛"),
        st.Page("pages/7_Accessorial_Tracker.py", title="Accessorial",   icon="📋"),
        st.Page("pages/9_Carrier_Lookup.py",     title="Carrier Lookup", icon="🔍"),
        st.Page("pages/chatbot.py",              title="Chatbot",        icon="💬"),
    ]

    if role == "admin":
        pages.append(st.Page("pages/8_Admin.py", title="Admin", icon="🛠️"))

    pg = st.navigation(pages, expanded=True)
    pg.run()

else:
    pg = st.navigation(
        [st.Page(_login_page, title="Sign In", icon="📦")],
        position="hidden",
    )
    pg.run()
