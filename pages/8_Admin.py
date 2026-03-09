# File: pages/8_Admin.py
import streamlit as st
import sys, os, json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth, logout
from utils.styling import inject_css, top_nav
from utils.database import get_connection, get_pace_users, create_pace_user, delete_pace_user

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
    st.error("Access denied. This page is for admins only.")
    st.page_link("pages/0_Home.py", label="Go to Home", icon="🏠")
    st.stop()

username = st.session_state.get("username", "admin")
top_nav(username)

conn = get_connection()

st.markdown("## Admin Panel")
st.caption(f"Logged in as **{username}** · Role: admin")
st.divider()

# ── User Management ────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### User Management")

    # Create user form
    with st.form("create_user_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_username = st.text_input("Username")
        with c2:
            new_password = st.text_input("Password", type="password")
        with c3:
            new_role = st.selectbox("Role", ["user", "admin"])

        submitted = st.form_submit_button("Create User", type="primary")
        if submitted:
            if not new_username or not new_password:
                st.error("Please fill in username and password.")
            else:
                err = create_pace_user(conn, new_username.strip(), new_password, new_role)
                if err:
                    st.error(err)
                else:
                    st.success(f"User '{new_username}' created with role '{new_role}'.")
                    st.cache_data.clear()

st.markdown("<br>", unsafe_allow_html=True)

# ── Current users table ────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Current Users")

    users_df = get_pace_users(conn)

    if users_df.empty:
        st.info("No users found in database.")
    else:
        # Delete controls
        deletable = [u for u in users_df["Username"].tolist() if u != username]
        col_tbl, col_del = st.columns([3, 1])
        with col_tbl:
            st.dataframe(users_df, use_container_width=True, hide_index=True)
        with col_del:
            if deletable:
                del_target = st.selectbox("Delete user", deletable, label_visibility="visible")
                if st.button("Delete", type="secondary"):
                    err = delete_pace_user(conn, del_target)
                    if err:
                        st.error(err)
                    else:
                        st.success(f"User '{del_target}' deleted.")
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.caption("No other users to delete.")

st.markdown("<br>", unsafe_allow_html=True)

# ── ML Pipeline info ───────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### ML Pipeline")
    st.caption("Run the pipeline from your terminal to retrain the model and update risk scores.")

    meta_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "model_metadata.json")

    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1: st.metric("Model", meta.get("model_name", "—"))
        with m2: st.metric("Accuracy", f"{meta.get('accuracy', 0):.2%}")
        with m3: st.metric("AUC-ROC", f"{meta.get('auc_roc', 0):.4f}")
        with m4: st.metric("Rows Trained", f"{meta.get('trained_on_rows', 0):,}")
        with m5: st.metric("Trained At", meta.get("trained_at", "—"))
    else:
        st.warning("No trained model found. Run the pipeline to generate one.", icon="⚠️")

    st.code("python scripts/ml_pipeline.py", language="bash")
    st.caption("Trains the model, scores all shipments, and writes risk_reason + recommended_action back to the database.")
