# File: app.py
import os
import base64
import streamlit as st

from auth_utils import check_auth


def _bg_css() -> str:
    """Return background CSS props for the ::before blur layer."""
    img_path = os.path.join(os.path.dirname(__file__), "assets", "background.png")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return (
            f"background-image:url('data:image/png;base64,{b64}');"
            "background-size:cover;background-position:center;"
        )
    return "background:linear-gradient(155deg,#060012 0%,#09021a 40%,#06010f 100%);"


_bg_props = _bg_css()

# ── Fallback users if DB unavailable ──────────────────────────────────────────
_FALLBACK = {
    "admin": {"password": "admin", "role": "admin"},
    "user":  {"password": "user",  "role": "user"},
}

st.set_page_config(
    page_title="PACE — Sign In",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",

)



# -------------------------

# Styling

# -------------------------

st.markdown(

    """

    <style>



    /* Hide sidebar */

    [data-testid="stSidebar"] {display:none;}

    [data-testid="collapsedControl"] {display:none;}



    /* White background */

    .stApp {

        background-color: white;

    }



    .block-container {

        padding-top: 3rem;

    }



    /* Login card */

    div[data-testid="stVerticalBlock"] > div:has(div.stForm){

        background: #F8FAFC;

        padding: 28px;

        border-radius: 12px;

        border: 1px solid #E5E7EB;

    }



    /* Vertical PACE area */

    .pace-wrap{

        height: 90vh;

        display:flex;

        align-items:center;

        justify-content:center;

    }



    .pace-vertical{

        font-size:170px;

        font-weight:900;

        line-height:0.9;

        letter-spacing:12px;

        color:#0F2B4A;

        text-align:center;

    }



    .pace-sub{

        margin-top:20px;

        font-size:18px;

        color:#6B7280;

        text-align:center;

    }



    .pace-foot{

        color:#9CA3AF;

        font-size:11px;

        margin-top:25px;

    }



    </style>

    """,

    unsafe_allow_html=True,

)



# -------------------------

# Already logged in

# -------------------------

if check_auth():

    role = st.session_state.get("role", "user")



    if role == "admin":

        st.switch_page("pages/8_Admin.py")

    else:

        st.switch_page("pages/0_Home.py")



    st.stop()



# -------------------------

# Demo users

# -------------------------

USERS = {

    "admin": {"password": "admin", "role": "admin"},

    "user": {"password": "user", "role": "user"},

}



# -------------------------

# Layout

# -------------------------

left, right = st.columns([1,1.6])



# -------------------------

# LEFT — LOGIN

# -------------------------

with left:



    st.markdown("### Sign in")



    with st.form("login_form"):

        username = st.text_input("Username")

        password = st.text_input("Password", type="password")



        submitted = st.form_submit_button(
            "Sign In", width="stretch", type="primary"
        )



    if submitted:



        u = (username or "").strip()

        p = password or ""



        if not u or not p:

            st.error("Please enter username and password")



        elif u in USERS and p == USERS[u]["password"]:



                st.session_state["authenticated"] = True
                st.session_state["username"] = u
                st.session_state["role"] = role
                st.session_state["_data_preloaded"] = False
                st.session_state["post_load_dest"] = (
                    "pages/8_Admin.py" if role == "admin" else "pages/0_Home.py"
                )
                st.switch_page("pages/loading.py")
            else:

                st.switch_page("pages/0_Home.py")



            st.stop()



        else:

            st.error("Invalid username or password")



    st.markdown(

        """

        <div class="pace-foot">

        © 2026 PACE · University of Arkansas · ISYS 43603

        </div>

        """,

        unsafe_allow_html=True

    )



# -------------------------

# RIGHT — HUGE PACE

# -------------------------

with right:



    st.markdown(

        """

        <div class="pace-wrap">



        <div>



        <div class="pace-vertical">

        P<br>

        A<br>

        C<br>

        E

        </div>



        <div class="pace-sub">

        Predictive Accessorial Cost Engine

        </div>



        </div>



        </div>

        """,

        unsafe_allow_html=True

    )