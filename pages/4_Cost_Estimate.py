# File: pages/4_Cost_Estimate.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.mock_data import generate_mock_shipments, CARRIERS, FACILITIES
from utils.styling import (
    inject_css, top_nav,
    CARD_BG, BORDER, PLUM,
    TEXT_PRIMARY, TEXT_SECONDARY,
    BRIGHT_TEAL, CORAL, LAVENDER,
    DARK_LAYOUT,
)

st.set_page_config(
    page_title="PACE — Cost Estimate",
    page_icon="P",
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


# ── Train model (cached) ───────────────────────────────────────────────────────
@st.cache_resource
def train_model():
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.pipeline import Pipeline

    df = generate_mock_shipments(300)
    df["total_cost_usd"] = df["base_freight_usd"] + df["accessorial_charge_usd"]

    cat_cols = ["carrier", "facility"]
    num_cols = ["weight_lbs", "miles"]

    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ("num", "passthrough", num_cols),
    ])
    model = Pipeline([
        ("pre", preprocessor),
        ("rf",  RandomForestRegressor(n_estimators=200, random_state=42)),
    ])
    X = df[cat_cols + num_cols]
    y = df["total_cost_usd"]
    model.fit(X, y)
    return model, df


@st.cache_data
def load_data():
    return generate_mock_shipments(300)


model, df_train = train_model()
df = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Cost Estimator")
st.caption(
    "Predict total shipment cost using a Random Forest ML model — "
    "more accurate than a flat average because it accounts for carrier, facility, weight, and distance."
)
st.divider()

# ── Input form + prediction ───────────────────────────────────────────────────
form_col, result_col = st.columns([2, 3], gap="large")

with form_col:
    with st.container(border=True):
        st.markdown("#### Shipment Details")
        st.caption("Enter shipment parameters to generate a cost prediction with confidence interval")
        carrier  = st.selectbox("Carrier",  sorted(CARRIERS))
        facility = st.selectbox("Facility", sorted(FACILITIES))
        weight   = st.number_input("Weight (lbs)", min_value=100, max_value=44_000,
                                   value=10_000, step=500)
        miles    = st.number_input("Miles", min_value=50, max_value=2_400,
                                   value=500, step=50)
        estimate_clicked = st.button("Estimate Cost →", type="primary",
                                     use_container_width=True)

    with st.expander("Model Info", expanded=False):
        st.markdown("""
**Algorithm:** Random Forest Regressor
**Training samples:** 300
**Features:** Carrier, Facility, Weight (lbs), Miles
**Target:** Total Shipment Cost (USD)
**Confidence interval:** 95% (±1.96σ across all tree predictions)
        """)

with result_col:
    avg_cpm    = df["cost_per_mile"].mean()
    avg_total  = df["total_cost_usd"].mean()
    simple_est = avg_cpm * miles

    if estimate_clicked:
        X_input = pd.DataFrame([{
            "carrier": carrier, "facility": facility,
            "weight_lbs": weight, "miles": miles,
        }])
        rf         = model.named_steps["rf"]
        X_trans    = model.named_steps["pre"].transform(X_input)
        tree_preds = np.array([t.predict(X_trans)[0] for t in rf.estimators_])
        pred       = tree_preds.mean()
        lower      = max(0, pred - 1.96 * tree_preds.std())
        upper      = pred + 1.96 * tree_preds.std()

        st.session_state["last_estimate"] = {
            "pred": pred, "lower": lower, "upper": upper,
            "simple_est": simple_est, "avg_total": avg_total,
            "carrier": carrier, "facility": facility,
            "weight": weight, "miles": miles,
        }

    if "last_estimate" in st.session_state:
        e = st.session_state["last_estimate"]
        pred, lower, upper = e["pred"], e["lower"], e["upper"]
        simple_est = e["simple_est"]

        with st.container(border=True):
            st.markdown("#### ML Cost Prediction")
            st.caption("Model output with 95% confidence bounds derived from individual tree variance")
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("Predicted Total Cost", f"${pred:,.2f}")
            with r2:
                st.metric("95% Lower Bound", f"${lower:,.2f}")
            with r3:
                st.metric("95% Upper Bound", f"${upper:,.2f}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='font-size:13px; color:{TEXT_SECONDARY};'>"
                f"Confidence range: <b style='color:{TEXT_PRIMARY};'>${lower:,.0f} – ${upper:,.0f}</b>"
                f" &nbsp;|&nbsp; Spread: <b style='color:{TEXT_PRIMARY};'>${upper - lower:,.0f}</b>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### How This Compares")
            st.caption("ML prediction vs two naive benchmarks — delta shows how much the model differs from simpler estimates")
            c1, c2, c3 = st.columns(3)
            delta_simple = pred - simple_est
            delta_avg    = pred - avg_total
            with c1:
                st.metric("ML Prediction",      f"${pred:,.2f}")
            with c2:
                st.metric("Avg Cost/Mile Est.", f"${simple_est:,.2f}",
                          delta=f"${delta_simple:+,.2f} vs ML", delta_color="inverse")
            with c3:
                st.metric("Fleet Avg Total",    f"${avg_total:,.2f}",
                          delta=f"${delta_avg:+,.2f} vs ML",    delta_color="inverse")

            st.markdown("<br>", unsafe_allow_html=True)
            comp_fig = go.Figure(go.Bar(
                x=["ML Prediction",
                   f"Avg Cost/Mile\n(${avg_cpm:.2f}/mi × {e['miles']} mi)",
                   "Fleet Avg Total"],
                y=[pred, simple_est, avg_total],
                marker_color=[BRIGHT_TEAL, BORDER, PLUM],
                text=[f"${v:,.0f}" for v in [pred, simple_est, avg_total]],
                textposition="outside",
                textfont=dict(color=TEXT_SECONDARY, size=11),
            ))
            comp_fig.update_layout(
                **DARK_LAYOUT,
                margin=dict(l=0, r=0, t=8, b=0), height=220,
                showlegend=False,
            )
            comp_fig.update_yaxes(tickprefix="$")
            st.plotly_chart(comp_fig, use_container_width=True)

    else:
        with st.container(border=True):
            st.markdown(
                f"<div style='text-align:center; padding:60px 20px; color:{TEXT_SECONDARY};'>"
                f"<div style='font-size:32px; line-height:1;'><svg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 24 24' fill='none' stroke='#38667E' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><line x1='12' y1='1' x2='12' y2='23'/><path d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'/></svg></div>"
                f"<div style='font-size:14px; margin-top:8px;'>"
                f"Fill in the shipment details and click <b>Estimate Cost</b></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)

# ── Feature importance ─────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### What Drives Cost — Feature Importance")
    st.caption(
        "Relative contribution of each input to model predictions — "
        "longer bars have more influence on the estimated cost"
    )

    rf      = model.named_steps["rf"]
    pre     = model.named_steps["pre"]
    enc     = pre.named_transformers_["cat"]
    cat_names = list(enc.get_feature_names_out(["carrier", "facility"]))
    all_names = cat_names + ["weight_lbs", "miles"]

    importance = pd.DataFrame({
        "Feature":    all_names,
        "Importance": rf.feature_importances_,
    }).sort_values("Importance", ascending=True).tail(12)

    importance["Feature"] = (
        importance["Feature"]
        .str.replace("carrier_", "Carrier: ", regex=False)
        .str.replace("facility_", "Facility: ", regex=False)
        .str.replace("weight_lbs", "Weight (lbs)", regex=False)
        .str.replace("miles", "Miles", regex=False)
    )

    fi_fig = go.Figure(go.Bar(
        x=importance["Importance"],
        y=importance["Feature"],
        orientation="h",
        marker_color=LAVENDER,
        marker_line_width=0,
        text=importance["Importance"].apply(lambda v: f"{v:.1%}"),
        textposition="outside",
        textfont=dict(color=TEXT_SECONDARY, size=11),
    ))
    fi_fig.update_layout(
        **DARK_LAYOUT, margin=dict(l=0, r=60, t=8, b=0), height=340,
    )
    fi_fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(fi_fig, use_container_width=True)

# ── Historical distribution ────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Historical Total Cost Distribution")
    st.caption(
        "Distribution of all historical shipment costs — "
        "the red dashed line shows where your predicted cost falls relative to the fleet"
    )

    hist_fig = go.Figure()
    hist_fig.add_trace(go.Histogram(
        x=df["total_cost_usd"], nbinsx=30,
        marker_color=BORDER,
        marker_line_color=BRIGHT_TEAL,
        marker_line_width=1,
        name="Historical",
        opacity=0.8,
    ))

    if "last_estimate" in st.session_state:
        hist_fig.add_vline(
            x=st.session_state["last_estimate"]["pred"],
            line_width=2, line_dash="dash", line_color=CORAL,
            annotation_text=f"Your estimate: ${st.session_state['last_estimate']['pred']:,.0f}",
            annotation_position="top right",
            annotation_font_color=CORAL,
        )

    hist_fig.update_layout(
        **DARK_LAYOUT, margin=dict(l=0, r=0, t=8, b=0), height=220, showlegend=False,
    )
    hist_fig.update_xaxes(tickprefix="$")
    st.plotly_chart(hist_fig, use_container_width=True)
