# File: pages/4_Cost_Estimate.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import get_connection, get_shipments
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav
from utils.cost_model import get_cost_model
from utils.risk_model import get_risk_model, predict_risk

st.set_page_config(
    page_title="PACE | Cost & Risk Predictor",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

# ── Load data ─────────────────────────────────────────────────────────────────
_conn   = get_connection()
_df_raw = get_shipments(_conn) if _conn is not None else pd.DataFrame()
if _df_raw.empty:
    _df_raw = generate_mock_shipments(300)
    st.info("Live database unavailable — showing demo data.")

df = _df_raw.copy()
if "AppointmentType" not in df.columns:
    df["AppointmentType"] = "Drop"
df["AppointmentType"] = df["AppointmentType"].fillna("Drop")

cost_model = get_cost_model(len(df), df)
risk_model, _ = get_risk_model(len(df), df)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _risk_color(score01: float) -> str:
    if score01 >= 0.70:
        return "#EF4444"
    if score01 >= 0.40:
        return "#F59E0B"
    return "#10B981"


def _risk_tier(score01: float) -> str:
    if score01 >= 0.70:
        return "High"
    if score01 >= 0.40:
        return "Medium"
    return "Low"


def _recommendation(tier: str, appt: str) -> str:
    if tier == "High":
        return "Consider adjusting appointment type/time or selecting a lower-risk carrier/facility combination."
    if tier == "Medium":
        return "Monitor for delays and consider adding a modest accessorial buffer in pricing."
    if str(appt).lower().strip() == "drop":
        return "Low risk profile — maintain standard plan; confirm drop procedures to keep dwell time low."
    return "Low risk profile — standard operating procedure applies."


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Risk Estimator")
st.caption("Enter shipment details to calculate accessorial risk and expected cost exposure.")
st.divider()

# ── Input form ────────────────────────────────────────────────────────────────
form_col, result_col = st.columns([2, 3], gap="large")

with form_col:
    with st.container(border=True):
        st.markdown("#### Shipment Details")
        carriers_list   = sorted(df["carrier"].dropna().unique())
        facilities_list = sorted(df["facility"].dropna().unique())
        appt_types_list = ["Live Load", "Drop", "Preloaded"]

        carrier  = st.selectbox("Carrier",          carriers_list)
        facility = st.selectbox("Facility",         facilities_list)
        appt     = st.selectbox("Appointment Type", appt_types_list)
        weight   = st.number_input("Weight (lbs)", min_value=100,  max_value=44_000,
                                   value=10_000, step=500)
        miles    = st.number_input("Miles",        min_value=50,   max_value=2_400,
                                   value=500,    step=50)
        estimate_clicked = st.button("Calculate Risk", type="primary", width="stretch")

    with st.expander("Model Info", expanded=False):
        st.markdown(f"""
**Cost model:** Random Forest Regressor
**Risk model:** LightGBM Regressor
**Training samples:** {len(df):,}
**Cost features:** Carrier, Facility, Weight, Miles
**Risk features:** Carrier, Facility, Appointment Type, Weight, Miles
**Risk target:** Accessorial risk score (0 – 1)
        """)

# ── Run predictions ───────────────────────────────────────────────────────────
with result_col:
    avg_cpm   = df["cost_per_mile"].mean()
    avg_total = df["total_cost_usd"].mean()

    if estimate_clicked:
        # Cost prediction
        X_cost = pd.DataFrame([{
            "carrier": carrier, "facility": facility,
            "weight_lbs": weight, "miles": miles,
        }])
        rf         = cost_model.named_steps["rf"]
        X_trans    = cost_model.named_steps["pre"].transform(X_cost)
        tree_preds = np.array([t.predict(X_trans)[0] for t in rf.estimators_])
        pred       = tree_preds.mean()
        lower      = max(0, pred - 1.96 * tree_preds.std())
        upper      = pred + 1.96 * tree_preds.std()

        # Risk prediction
        risk = predict_risk(risk_model, carrier, facility, appt, weight, miles, df)

        st.session_state["last_estimate"] = {
            "pred": pred, "lower": lower, "upper": upper,
            "simple_est": avg_cpm * miles, "avg_total": avg_total,
            "carrier": carrier, "facility": facility,
            "appt": appt, "weight": weight, "miles": miles,
            "risk": risk,
        }
        # Append to history
        hist = st.session_state.get("estimator_history", [])
        hist = list(hist)
        hist.insert(0, {
            "ts": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "carrier": carrier,
            "facility": facility,
            "appointment_type": appt,
            "weight_lbs": int(weight),
            "miles": int(miles),
            "risk_score": float(risk["score"]) if risk else 0.0,
            "risk_tier": str(risk["tier"]) if risk else "—",
            "expected_cost": float(risk.get("expected_cost", 0.0)) if risk else 0.0,
        })
        st.session_state["estimator_history"] = hist[:25]

    if "last_estimate" in st.session_state:
        e    = st.session_state["last_estimate"]
        pred, lower, upper = e["pred"], e["lower"], e["upper"]
        risk = e.get("risk")

        # ── Results summary (Risk + Expected Cost) ─────────────────────────────
        if risk:
            score01 = float(risk.get("score", 0.0))
            tier = _risk_tier(score01)
            color = _risk_color(score01)
            exp_cost = float(risk.get("expected_cost", 0.0))

            top_left, top_right = st.columns([2, 3], gap="medium")
            with top_left:
                with st.container(border=True):
                    st.markdown("#### Risk Score")
                    st.markdown(
                        f"<div style='font-size:46px;font-weight:800;line-height:1;"
                        f"margin:6px 0;color:{color};'>{score01*100:.0f}%</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='display:inline-flex;align-items:center;"
                        f"padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700;"
                        f"border:1px solid rgba(241,245,249,0.14);"
                        f"background:rgba(255,255,255,0.04);color:{color};'>"
                        f"{tier} Risk</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.metric("Expected Cost Estimate", f"${exp_cost:,.0f}")
                    st.caption(_recommendation(tier, e.get("appt", "")))

            with top_right:
                with st.container(border=True):
                    st.markdown("#### Key Drivers")
                    st.caption("Top factors contributing to this prediction")
                    for label, detail, sev in risk.get("factors", []):
                        sev_fg = {"high": "#EF4444", "low": "#10B981", "neutral": "#2DD4BF"}.get(sev, "#2DD4BF")
                        sev_bg = {"high": "rgba(239,68,68,0.10)", "low": "rgba(16,185,129,0.10)", "neutral": "rgba(45,212,191,0.10)"}.get(sev, "rgba(45,212,191,0.10)")
                        st.markdown(
                            f"<div style='background:{sev_bg};border-left:3px solid {sev_fg};"
                            f"border-radius:10px;padding:10px 12px;margin-bottom:10px;'>"
                            f"<div style='color:{sev_fg};font-size:12px;font-weight:700;margin-bottom:2px;'>{label}</div>"
                            f"<div style='color:#CBD5E1;font-size:12px;line-height:1.5;'>{detail}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

            st.markdown("<br>", unsafe_allow_html=True)

        # ── Cost context ───────────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("#### Cost Context")
            st.caption("ML cost prediction with confidence range and comparison baselines")
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("Predicted Total Cost", f"${pred:,.0f}")
            with r2:
                st.metric("95% Lower Bound", f"${lower:,.0f}")
            with r3:
                st.metric("95% Upper Bound", f"${upper:,.0f}")

            st.markdown("<br>", unsafe_allow_html=True)
            simple_est = e["simple_est"]
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("ML Prediction", f"${pred:,.0f}")
            with c2:
                st.metric("Avg Cost/Mile Est.", f"${simple_est:,.0f}", delta=f"${pred - simple_est:+,.0f}")
            with c3:
                st.metric("Fleet Avg Total", f"${avg_total:,.0f}", delta=f"${pred - avg_total:+,.0f}")

    else:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center;padding:80px 20px;color:#9CA3AF;'>"
                "<div style='font-size:14px;margin-top:10px;'>"
                "Fill in shipment details and click <b>Calculate Risk</b></div>"
                "</div>",
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)

# ── Optional history ──────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Recent Calculations")
    hist = st.session_state.get("estimator_history", [])
    if not hist:
        st.caption("No calculations yet. Run the estimator to see history here.")
    else:
        hist_df = pd.DataFrame(hist)
        st.dataframe(
            hist_df.rename(columns={
                "ts": "Time",
                "carrier": "Carrier",
                "facility": "Facility",
                "appointment_type": "Appointment Type",
                "weight_lbs": "Weight (lbs)",
                "miles": "Miles",
                "risk_score": "Risk Score",
                "risk_tier": "Risk Tier",
                "expected_cost": "Expected Cost ($)",
            }),
            width="stretch",
            hide_index=True,
            column_config={
                "Risk Score": st.column_config.ProgressColumn(
                    "Risk Score", format="%.0f%%", min_value=0, max_value=1
                ),
                "Expected Cost ($)": st.column_config.NumberColumn(format="$%.0f"),
            },
            height=260,
        )
