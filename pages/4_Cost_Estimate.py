# File: pages/4_Cost_Estimate.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import get_connection, get_shipments, get_carriers
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav, NAVY_500, NAVY_100
from utils import ml

st.set_page_config(
    page_title="PACE — Cost Estimate",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

# ── Load data ─────────────────────────────────────────────────────────────────
_conn = get_connection()
_df_raw = get_shipments(_conn) if _conn is not None else pd.DataFrame()
if _df_raw.empty:
    _df_raw = generate_mock_shipments(300)
    st.info("Live database unavailable — showing demo data.", icon="ℹ️")

df = _df_raw.copy()

# ── Load saved model ───────────────────────────────────────────────────────────
model, metrics = ml.load_model()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Cost Estimator")
st.caption("Predict total shipment cost using machine learning — trained on your historical shipments.")
st.divider()

# ── Train / metrics row ───────────────────────────────────────────────────────
ctrl_col, metric_col = st.columns([1, 3])

with ctrl_col:
    with st.container(border=True):
        if model is None:
            st.warning("No model trained yet.")
            btn_label = "Train Model"
        else:
            st.success("Model ready")
            btn_label = "Retrain Model"

        if st.button(btn_label, type="primary", use_container_width=True, disabled=_conn is None):
            with st.spinner("Training on all shipment data..."):
                model, metrics = ml.train(_conn)
            st.success("Training complete!")
            st.rerun()

        if _conn is None:
            st.caption("Database required to train.")

with metric_col:
    if metrics:
        with st.container(border=True):
            st.markdown("#### Model Performance (held-out 20% test set)")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("MAE", f"${metrics['mae']:,.2f}",
                      help="Mean Absolute Error — average dollar error on unseen shipments")
            m2.metric("RMSE", f"${metrics['rmse']:,.2f}",
                      help="Root Mean Squared Error — penalizes large errors more heavily")
            m3.metric("R²", f"{metrics['r2']:.3f}",
                      help="1.0 = perfect predictions, 0.0 = no better than a flat average")
            m4.metric("Training Samples", f"{metrics['n_train']:,}")

st.divider()

# ── Carrier & dwell lookup ────────────────────────────────────────────────────
carriers_df = get_carriers(_conn) if _conn is not None else pd.DataFrame()
if not carriers_df.empty:
    carrier_options = {
        row["carrier_name"]: row["carrier_id"]
        for _, row in carriers_df.iterrows()
    }
else:
    carrier_options = {"Demo Carrier A": 1, "Demo Carrier B": 2}

facility_types = ["Cold Storage", "Cross-Dock", "Distribution Center", "Receiver", "Shipper", "Warehouse"]
appt_types     = ["Drop", "FCFS", "Live"]
dwell_defaults = {
    "Cold Storage": 6.0, "Cross-Dock": 2.0, "Distribution Center": 5.0,
    "Receiver": 4.0, "Shipper": 3.5, "Warehouse": 5.5,
}
now = datetime.now()

# ── Input form + result ───────────────────────────────────────────────────────
form_col, result_col = st.columns([2, 3], gap="large")

with form_col:
    with st.container(border=True):
        st.markdown("#### Shipment Details")
        carrier_name  = st.selectbox("Carrier", list(carrier_options.keys()))
        facility_type = st.selectbox("Facility Type", facility_types)
        appt_type     = st.selectbox("Appointment Type", appt_types)
        distance      = st.number_input("Distance (miles)", min_value=50, max_value=3000, value=500, step=50)
        weight        = st.number_input("Weight (lbs)", min_value=500, max_value=44000, value=10000, step=500)

        with st.expander("Advanced", expanded=False):
            dwell     = st.number_input(
                "Avg Dwell Time (hrs)", min_value=0.5, max_value=24.0,
                value=dwell_defaults.get(facility_type, 4.0), step=0.5,
            )
            ship_month = st.selectbox(
                "Ship Month", list(range(1, 13)), index=now.month - 1,
                format_func=lambda m: datetime(2024, m, 1).strftime("%B"),
            )
            ship_dow = st.selectbox(
                "Day of Week", list(range(7)), index=now.weekday(),
                format_func=lambda d: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d],
            )

        estimate_clicked = st.button(
            "Estimate Cost →", type="primary",
            use_container_width=True, disabled=model is None,
        )
        if model is None:
            st.caption("Train the model above first.")

    with st.expander("ℹ️ Model Info", expanded=False):
        if metrics:
            st.markdown(f"""
**Algorithm:** LightGBM Gradient Boosting
**Features:** Carrier, Facility Type, Appointment Type, Distance, Weight, Dwell Time, Month, Day of Week
**Target:** Total Cost (Linehaul + Accessorial)
**Training rows:** {metrics['n_train']:,} &nbsp;|&nbsp; **Test rows:** {metrics['n_test']:,}
            """)
        else:
            st.markdown("Model not yet trained.")

with result_col:
    avg_total  = df["total_cost_usd"].mean() if not df.empty else 0
    avg_cpm    = df["cost_per_mile"].mean()   if not df.empty else 0
    simple_est = avg_cpm * distance

    if estimate_clicked and model is not None:
        pred = ml.predict(
            model,
            carrier_id     = carrier_options[carrier_name],
            facility_type  = facility_type,
            appointment_type = appt_type,
            distance       = distance,
            weight         = weight,
            dwell_time     = dwell,
            month          = ship_month,
            day_of_week    = ship_dow,
        )
        pred = max(0.0, pred)
        st.session_state["last_estimate"] = {
            "pred": pred, "simple_est": simple_est, "avg_total": avg_total,
            "carrier": carrier_name, "facility": facility_type,
            "weight": weight, "miles": distance,
        }

    if "last_estimate" in st.session_state:
        e    = st.session_state["last_estimate"]
        pred = e["pred"]

        with st.container(border=True):
            st.markdown("#### ML Cost Prediction")
            r1, r2 = st.columns(2)
            r1.metric("Predicted Total Cost", f"${pred:,.2f}",
                      help="ML model's estimate of the total shipment cost — linehaul plus expected accessorial charges.")
            pct = ((pred - avg_total) / avg_total * 100) if avg_total else 0
            r2.metric("vs Fleet Average", f"${avg_total:,.2f}",
                      delta=f"{pct:+.1f}%", delta_color="inverse",
                      help="Your fleet's historical average total cost. Positive delta means this shipment is predicted to cost more than average.")

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### How This Compares")
            c1, c2, c3 = st.columns(3)
            c1.metric("ML Prediction",      f"${pred:,.2f}",
                      help="Cost predicted by the LightGBM model using carrier, facility, distance, weight, and seasonality.")
            c2.metric("Avg Cost/Mile Est.", f"${e['simple_est']:,.2f}",
                      delta=f"${e['simple_est'] - pred:+,.2f} vs ML", delta_color="inverse",
                      help="Simple estimate using fleet average cost-per-mile x distance. Less accurate than the ML model.")
            c3.metric("Fleet Avg Total",    f"${avg_total:,.2f}",
                      delta=f"${avg_total - pred:+,.2f} vs ML", delta_color="inverse",
                      help="Historical average total cost across all shipments — a naive baseline with no shipment-specific context.")

            st.markdown("<br>", unsafe_allow_html=True)
            comp_fig = go.Figure(go.Bar(
                x=["ML Prediction", "Avg Cost/Mile Est.", "Fleet Avg Total"],
                y=[pred, e["simple_est"], avg_total],
                marker_color=[NAVY_500, "#9CA3AF", "#D1D5DB"],
                text=[f"${v:,.0f}" for v in [pred, e["simple_est"], avg_total]],
                textposition="outside",
            ))
            comp_fig.update_layout(
                margin=dict(l=0, r=0, t=8, b=0), height=220,
                plot_bgcolor="white", paper_bgcolor="white",
                yaxis=dict(tickprefix="$", gridcolor="#F3F4F6"),
                xaxis=dict(gridcolor="#F3F4F6"),
                showlegend=False,
            )
            st.plotly_chart(comp_fig, use_container_width=True)

    else:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center; padding:60px 20px; color:#9CA3AF;'>"
                "<div style='font-size:32px;'>💰</div>"
                "<div style='font-size:14px; margin-top:8px;'>"
                "Fill in the shipment details and click <b>Estimate Cost</b></div>"
                "</div>",
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)

# ── Feature importance ────────────────────────────────────────────────────────
if model is not None:
    with st.container(border=True):
        st.markdown("#### What Drives Cost — Feature Importance")
        st.caption("Relative contribution of each input to the model's predictions")

        importance = ml.get_feature_importance(model)
        fi_fig = go.Figure(go.Bar(
            x=importance["Importance"],
            y=importance["Feature"],
            orientation="h",
            marker_color=NAVY_500,
            text=importance["Importance"].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
        ))
        fi_fig.update_layout(
            margin=dict(l=0, r=80, t=8, b=0), height=300,
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(gridcolor="#F3F4F6"),
            yaxis=dict(gridcolor="#F3F4F6"),
        )
        st.plotly_chart(fi_fig, use_container_width=True)

# ── Historical distribution ───────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Historical Total Cost Distribution")
    st.caption("See where your prediction falls relative to past shipments")

    hist_fig = go.Figure()
    hist_fig.add_trace(go.Histogram(
        x=df["total_cost_usd"], nbinsx=30,
        marker_color=NAVY_100, marker_line_color=NAVY_500, marker_line_width=1,
    ))

    if "last_estimate" in st.session_state:
        p = st.session_state["last_estimate"]["pred"]
        hist_fig.add_vline(
            x=p, line_width=2, line_dash="dash", line_color="#DC2626",
            annotation_text=f"Your estimate: ${p:,.0f}",
            annotation_position="top right",
            annotation_font_color="#DC2626",
        )

    hist_fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0), height=220,
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(tickprefix="$", gridcolor="#F3F4F6"),
        yaxis=dict(gridcolor="#F3F4F6"),
        showlegend=False,
    )
    st.plotly_chart(hist_fig, use_container_width=True)
