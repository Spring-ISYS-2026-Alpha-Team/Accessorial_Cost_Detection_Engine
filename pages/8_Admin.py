import streamlit as st

from auth_utils import check_auth



# -------------------------

# Page config

# -------------------------

st.set_page_config(

    page_title="PACE — Admin",

    page_icon="🛠️",

    layout="wide"

)



# -------------------------

# Authentication check

# -------------------------

if not check_auth():

    st.warning("Please sign in first.")

    st.page_link("app.py", label="Go to Sign In", icon="🔐")

    st.stop()



# -------------------------

# Role check

# -------------------------

role = st.session_state.get("role", "user")



if role != "admin":

    st.error("Access denied. Admins only.")

    st.page_link("pages/0_Home.py", label="Go to Home", icon="🏠")

    st.stop()



# -------------------------

# Admin header

# -------------------------

st.title("🛠️ Admin Panel")

st.caption("This page is only visible to users with the admin role.")



st.write("Logged in as:", st.session_state.get("username"))

st.write("Role:", role)



st.divider()



# -------------------------

# User Management

# -------------------------

st.subheader("User Management")



st.info(

    "This is a prototype for user management. "

    "Next step will be connecting this form to the Azure SQL users table."

)



# Create user form

with st.form("create_user_form"):

    new_username = st.text_input("Username")

    new_password = st.text_input("Password", type="password")

    new_role = st.selectbox("Role", ["user", "admin"])



    submitted = st.form_submit_button("Create User")



    if submitted:

        if not new_username or not new_password:

            st.error("Please fill in username and password.")

        else:

            st.success(

                f"User '{new_username}' created with role '{new_role}' (demo only)."

            )



st.divider()



# -------------------------

# Demo users table

# -------------------------

st.subheader("Current Users (Demo)")



demo_users = [

    {"username": "admin", "role": "admin"},

    {"username": "user", "role": "user"}

]



st.table(demo_users)



st.divider()



# -------------------------

# Logout button

# -------------------------

if st.button("Log out"):

    for k in ["authenticated", "username", "role"]:

        st.session_state.pop(k, None)



    st.switch_page("app.py")