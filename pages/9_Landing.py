import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.styling import inject_css


st.set_page_config(
    page_title="PACE | Homepage",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()


if check_auth():
    st.switch_page("pages/0_Home.py")


def _nav():
    logo_col, _ = st.columns([1, 3])
    with logo_col:
        st.markdown(
            "<div style='font-weight:900;letter-spacing:3.33px;font-size:100px;'>PACE</div>",
            unsafe_allow_html=True,
        )


_nav()

# ── HERO SECTION (inspired by HTML design, brown/white palette) ───────────────
hero_left, hero_right = st.columns([1.2, 1.0], gap="small")

with hero_left:
    st.markdown(
        "<div style='display:inline-flex;align-items:center;gap:6px;"
        "font-size:11px;font-weight:500;letter-spacing:0.12em;text-transform:uppercase;"
        "color:#ffffff;background:rgba(255,255,255,0.06);border:0.3px solid rgba(255,255,255,0.25);"
        "padding:0.3rem 0.75rem;border-radius:999px;margin-bottom:1.5rem;'>"
        "<span style='width:6px;height:6px;border-radius:50%;background:#f9f9f3;'></span>"
        "Predictive Accessorial Cost Engine"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h1 style='font-size:clamp(2rem,4vw,3rem);font-weight:300;line-height:1.15;"
        "color:#ffffff;margin-bottom:1.25rem;letter-spacing:-0.02em;'>"
        "Predict accessorial costs<br><strong style='font-weight:600;color:#ffffff;'>"
        "BEFORE they hit your margin.</strong></h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='font-size:15px;color:rgba(249,249,243,0.70);line-height:1.7;"
        "margin-bottom:2rem;max-width:440px;'>"
        "PACE turns historical shipment data into forward-looking risk scores and cost exposure so "
        "your team can quote confidently and avoid surprise charges."
        "</p>",
        unsafe_allow_html=True,
    )
    cta_col, _ = st.columns([1, 1])
    with cta_col:
        # Scoped style so only this CTA uses the pink gradient from the login page
        st.markdown(
            """
            <style>
            #landing-cta button {
                background: linear-gradient(135deg, #9333EA, #C2185B) !important;
                color: #ffffff !important;
                border: 1px !important;
                border-radius: 4px !important;
                font-size: 33px !important;
                letter-spacing: 0.08em !important;
                text-transform: uppercase !important;
                padding: 14px 32px !important;
            }
            #landing-cta button:hover {
                filter: brightness(1.05);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        with st.container():
            st.markdown("<div id='landing-cta'>", unsafe_allow_html=True)
            if st.button("Get started in PACE", key="landing_cta_primary"):
                st.session_state["show_login"] = True
                st.switch_page("app.py")
            st.markdown("</div>", unsafe_allow_html=True)

  
with hero_right:
    st.markdown(
        """
        <div style="background:#1b130b;border-radius:16px;border:1px solid rgba(255,255,255,0.10);
                    padding:1.5rem;position:relative;overflow:hidden;">
          <div style="position:absolute;top:0;left:0;right:0;height:1px;
                      background:linear-gradient(90deg,transparent,rgba(255,255,255,0.55),transparent);"></div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem;">
            <div style="font-size:12px;font-weight:500;color:rgba(249,249,243,0.7);letter-spacing:0.08em;
                        text-transform:uppercase;">PACE risk snapshot</div>
            <span style="font-size:11px;font-weight:500;padding:0.2rem 0.6rem;border-radius:999px;
                         background:rgba(239,68,68,0.15);color:#fecaca;border:0.5px solid rgba(239,68,68,0.35);">
              High risk lane
            </span>
          </div>
          <div style="font-size:2rem;font-weight:300;color:#ffffff;margin-bottom:0.25rem;">78%</div>
          <div style="font-size:12px;color:rgba(249,249,243,0.6);margin-bottom:1.25rem;">
            Probability of accessorials on DFW → MEM this week
          </div>
          <div style="background:rgba(255,255,255,0.08);border-radius:999px;height:5px;margin-bottom:1.25rem;overflow:hidden;">
            <div style="height:100%;width:78%;border-radius:999px;background:#f9f9f3;"></div>
          </div>
          <div style="display:flex;flex-direction:column;gap:0.6rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:0.5rem 0.75rem;background:rgba(255,255,255,0.03);
                        border-radius:7px;border:0.5px solid rgba(255,255,255,0.06);font-size:12px;">
              <span style="color:rgba(249,249,243,0.70);">Avg dwell (hrs)</span>
              <span style="font-family:monospace;font-size:11px;color:#fecaca;">3.4</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:0.5rem 0.75rem;background:rgba(255,255,255,0.03);
                        border-radius:7px;border:0.5px solid rgba(255,255,255,0.06);font-size:12px;">
              <span style="color:rgba(249,249,243,0.70);">High-risk carriers</span>
              <span style="font-family:monospace;font-size:11px;color:#fde68a;">3</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:0.5rem 0.75rem;background:rgba(255,255,255,0.03);
                        border-radius:7px;border:0.5px solid rgba(255,255,255,0.06);font-size:12px;">
              <span style="color:rgba(249,249,243,0.70);">Est. exposure</span>
              <span style="font-family:monospace;font-size:11px;color:#bbf7d0;">$4.2k</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── STAT STRIP + FEATURE GRID (continuous dark section) ───────────────────────
st.markdown(
    """
    <div style="background:#0e0e1a;border-top:1px solid rgba(255,255,255,0.08);
                padding:60px 80px 54px;">
      <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1.5rem;">
        <div style="padding-right:2.5rem;border-right:1px solid rgba(255,255,255,0.07);">
          <div style="font-size:2.5rem;font-weight:300;color:#ffffff;">15–20%</div>
          <p style="font-size:13px;color:rgba(255,255,255,0.45);margin-top:4px;">
            of shipments typically carry hidden accessorial risk
          </p>
        </div>
        <div style="padding:0 2.5rem;border-right:1px solid rgba(255,255,255,0.07);">
          <div style="font-size:2.5rem;font-weight:300;color:#ffffff;">72%</div>
          <p style="font-size:13px;color:rgba(255,255,255,0.45);margin-top:4px;">
            reduction in surprise charges for PACE users (demo stats)
          </p>
        </div>
        <div style="padding:0 2.5rem;border-right:1px solid rgba(255,255,255,0.07);">
          <div style="font-size:2.5rem;font-weight:300;color:#ffffff;">4</div>
          <p style="font-size:13px;color:rgba(255,255,255,0.45);margin-top:4px;">
            core workspaces: Dashboards, Routes, Carriers, Accessorial
          </p>
        </div>
        <div style="padding-left:2.5rem;">
          <div style="font-size:2.5rem;font-weight:300;color:#ffffff;">90 sec</div>
          <p style="font-size:13px;color:rgba(255,255,255,0.45);margin-top:4px;">
            to run your first risk estimate
          </p>
        </div>
      </div>

      <h3 style="font-size:20px;font-weight:400;color:#f0f0ee;margin:1.9rem 0 4px;">
        Everything you need to ship with confidence
      </h3>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);margin-bottom:1.4rem;">
        PACE connects your shipments, carriers, and lanes into a single view, so every quote and load plan
        accounts for accessorial risk up front.
      </p>

      <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1.5rem;">
        <div>
          <h4 style="font-size:15px;font-weight:500;color:#ffffff;">Risk Prediction</h4>
          <p style="font-size:13px;color:rgba(255,255,255,0.5);margin-top:4px;">
            ML-powered accessorial probability scoring across shipments, lanes, and facilities.
          </p>
        </div>
        <div>
          <h4 style="font-size:15px;font-weight:500;color:#ffffff;">Cost Estimation</h4>
          <p style="font-size:13px;color:rgba(255,255,255,0.5);margin-top:4px;">
            Expected dollar impact estimates to help you price with confidence.
          </p>
        </div>
        <div>
          <h4 style="font-size:15px;font-weight:500;color:#ffffff;">Carrier Analytics</h4>
          <p style="font-size:13px;color:rgba(255,255,255,0.5);margin-top:4px;">
            Performance insights by carrier so you can steer freight to the best partners.
          </p>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
