# File: auth_utils.py



import streamlit as st



# ---------------------------------------------------

# MOCK USER DATABASE (later you can replace with SQL)

# ---------------------------------------------------



USERS = {

    "admin": {

        "password": "admin123",

        "role": "admin"

    },

    "analyst": {

        "password": "analyst123",

        "role": "analyst"

    },

    "viewer": {

        "password": "viewer123",

        "role": "viewer"

    }

}





# ---------------------------------------------------

# LOGIN FUNCTION

# ---------------------------------------------------



def login(username, password):



    if username in USERS and USERS[username]["password"] == password:



        st.session_state["authenticated"] = True

        st.session_state["username"] = username

        st.session_state["role"] = USERS[username]["role"]



        return True



    return False





# ---------------------------------------------------

# LOGOUT

# ---------------------------------------------------



def logout():

    """

    Secure logout

    """



    for key in list(st.session_state.keys()):

        del st.session_state[key]



    st.cache_data.clear()

    st.cache_resource.clear()



    st.switch_page("app.py")





# ---------------------------------------------------

# CHECK AUTH

# ---------------------------------------------------



def check_auth():



    if not st.session_state.get("authenticated", False):



        st.warning("Please login to continue.")

        st.stop()



    return True





# ---------------------------------------------------

# GET USER ROLE

# ---------------------------------------------------



def get_role():



    return st.session_state.get("role", "viewer")





# ---------------------------------------------------

# REQUIRE ADMIN ACCESS

# ---------------------------------------------------



def require_admin():



    role = get_role()



    if role != "admin":

        st.error("Admin access required.")

        st.stop()





# ---------------------------------------------------

# REQUIRE ANALYST OR ADMIN

# ---------------------------------------------------



def require_analyst():



    role = get_role()



    if role not in ["admin", "analyst"]:

        st.error("You do not have permission to access this page.")

        st.stop()





# ---------------------------------------------------

# SHOW USER INFO (optional helper)

# ---------------------------------------------------



def show_user_info():



    username = st.session_state.get("username", "Unknown")

    role = st.session_state.get("role", "viewer")



    st.caption(f"Logged in as **{username}** | Role: **{role}**")