# File: pages/8_Admin.py
import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import get_connection, get_pace_users, create_pace_user, delete_pace_user
from utils.styling import inject_css, top_nav, ACCENT_SOFT, TEXT_PRIMARY, TEXT_SECONDARY

st.set_page_config(
    page_title="PACE — Admin",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

role = st.session_state.get("role", "user")
if role != "admin":
    st.error("Access denied. Admins only.")
    st.page_link("pages/0_Home.py", label="Go to Home", icon="🏠")
    st.stop()

username = st.session_state.get("username", "Admin")
top_nav(username)

conn = get_connection()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Admin Panel")
st.caption(f"Logged in as **{username}** · admin")
st.divider()

# ── User Management ───────────────────────────────────────────────────────────
col_form, col_users = st.columns([1, 2], gap="large")

with col_form:
    with st.container(border=True):
        st.markdown("#### Create User")
        with st.form("create_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["user", "admin"])
            submitted = st.form_submit_button("Create User", width="stretch", type="primary")
            if submitted:
                if not new_username or not new_password:
                    st.error("Username and password are required.")
                elif conn is None:
                    st.warning("No DB connection — cannot create user.")
                else:
                    ok, msg = create_pace_user(conn, new_username, new_password, new_role)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(f"Failed: {msg}")

with col_users:
    with st.container(border=True):
        st.markdown("#### Current Users")
        if conn is None:
            st.warning("No database connection — showing fallback accounts only.")
            st.dataframe(
                [{"username": "admin", "role": "admin"}, {"username": "user", "role": "user"}],
                width="stretch", hide_index=True,
            )
        else:
            users_df = get_pace_users(conn)
            if users_df.empty:
                st.info("No users found in PaceUsers table.")
            else:
                st.dataframe(users_df, width="stretch", hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("#### Delete User")
        if conn is not None:
            users_df2 = get_pace_users(conn)
            deletable = [u for u in users_df2["username"].tolist() if u != username] if not users_df2.empty else []
            if deletable:
                del_user = st.selectbox("Select user to delete", deletable, key="del_user_sel")
                if st.button("Delete User", type="primary"):
                    ok, msg = delete_pace_user(conn, del_user)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(f"Failed: {msg}")
            else:
                st.caption("No other users to delete.")
        else:
            st.caption("Database unavailable.")
