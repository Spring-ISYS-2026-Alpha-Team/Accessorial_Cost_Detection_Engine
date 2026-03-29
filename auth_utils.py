# File: auth_utils.py
import streamlit as st

def logout():
    """
    PB-4: Securely terminates the user session and redirects to login.
    Clears all session state and cached data.
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.cache_data.clear()
    # Intentionally NOT clearing cache_resource so the ML model
    # stays loaded in memory between sessions for faster reloads.
    st.switch_page("app.py")

def check_auth():
    """
    Helper to verify if user is logged in.
    Returns True if authenticated, False otherwise.
    """
    return st.session_state.get('authenticated', False)


def require_auth() -> None:
    """
    Auth guard for protected pages.
    Redirects immediately to login if not authenticated — no prompt shown,
    so navigating directly to any page URL just bounces to login cleanly.
    """
    if not check_auth():
        st.switch_page("app.py")
        st.stop()