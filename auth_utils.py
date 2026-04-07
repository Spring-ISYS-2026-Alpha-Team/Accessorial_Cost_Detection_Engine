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
    Uses st.switch_page to redirect unauthenticated users to login.
    Only called when a page is accessed directly without a session.
    """
    if not check_auth():
        st.switch_page("pages/1_Login.py")
        st.stop()
