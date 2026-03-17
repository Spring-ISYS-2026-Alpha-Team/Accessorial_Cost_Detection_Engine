import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import get_connection, create_pace_user
from utils.styling import inject_css


st.set_page_config(
    page_title="PACE | Create Account",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inject_css()

if check_auth():
    st.switch_page("pages/0_Home.py")

st.markdown("## Create your PACE account")
st.caption("Roles: Analyst or Viewer (Admin is assigned separately).")

with st.form("register_form"):
    full_name = st.text_input("Full name")
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm password", type="password")
    role = st.selectbox("Role", ["analyst", "viewer"])
    terms = st.checkbox("I agree to the Terms of Service")
    privacy = st.checkbox("I agree to the Privacy Policy")

    submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

if submitted:
    if not (full_name and email and username and password and confirm):
        st.error("Please complete all fields.")
    elif password != confirm:
        st.error("Passwords do not match.")
    elif not (terms and privacy):
        st.error("Please accept the Terms and Privacy Policy.")
    else:
        conn = get_connection()
        if conn is None:
            st.warning("Database is unavailable — account creation is disabled in demo mode.")
        else:
            ok, msg = create_pace_user(conn, username=username, password=password, role=role)
            if ok:
                st.success(msg)
                st.page_link("app.py", label="Continue to Sign In")
            else:
                st.error(f"Unable to create account: {msg}")

st.divider()
st.page_link("app.py", label="Back to Login")
st.page_link("pages/9_Landing.py", label="Back to Home")

