# File: app.py
import streamlit as st
from auth_utils import check_auth

st.set_page_config(
    page_title="PACE — Sign In",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Hide sidebar entirely on the login page
st.markdown("""
<style>
[data-testid="stSidebar"]       { display: none; }
[data-testid="collapsedControl"] { display: none; }
</style>
""", unsafe_allow_html=True)

# Already logged in → go straight to home
if check_auth():
    st.switch_page("pages/0_Home.py")

# ── Page layout ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:48px 0 28px;">
    <div style="font-size:48px; line-height:1;">📦</div>
    <h1 style="font-size:34px; font-weight:700; color:#0F2B4A;
               margin:10px 0 4px; letter-spacing:2px;">PACE</h1>
    <p style="color:#6B7280; font-size:14px; margin:0; letter-spacing:0.3px;">
        Predictive Accessorial Cost Engine
    </p>
</div>
""", unsafe_allow_html=True)

# ── Login card ────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Sign in to your account")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input(
            "Password", type="password", placeholder="Enter your password"
        )
        submitted = st.form_submit_button(
            "Sign In", use_container_width=True, type="primary"
        )

    if submitted:
        if username and password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.switch_page("pages/0_Home.py")
        else:
            st.error("Please enter both username and password.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="text-align:center; color:#9CA3AF; font-size:11px; margin-top:40px;">
    © 2026 PACE &nbsp;·&nbsp; University of Arkansas &nbsp;·&nbsp; ISYS 43603
</p>
""", unsafe_allow_html=True)
