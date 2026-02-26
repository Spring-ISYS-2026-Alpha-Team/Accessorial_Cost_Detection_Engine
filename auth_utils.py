# File: auth_utils.py
import streamlit as st

def logout():
    """
    PB-4: Securely terminates the user session.
    Clears all Streamlit session state variables to protect data access.
    """
    # Clear authentication flags
    if 'authenticated' in st.session_state:
        del st.session_state['authenticated']
    if 'username' in st.session_state:
        del st.session_state['username']
    
    # Clear any cached data that might persist
    st.cache_data.clear()
    st.cache_resource.clear()
    
    # Force rerun to redirect to login screen immediately
    st.rerun()

def check_auth():
    """
    Helper to verify if user is logged in.
    Returns True if authenticated, False otherwise.
    """
    return st.session_state.get('authenticated', False)