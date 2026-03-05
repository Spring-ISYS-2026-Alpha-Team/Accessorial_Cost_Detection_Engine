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
    st.cache_resource.clear()
    st.switch_page("app.py")

def check_auth():
    """
    Helper to verify if user is logged in.
    Returns True if authenticated, False otherwise.
    """
    return st.session_state.get('authenticated', False)