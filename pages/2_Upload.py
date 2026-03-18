# File: pages/2_Upload.py
import os
import sys
import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import require_auth
from utils.doc_parser import parse_uploaded_document
from utils.styling import inject_css, top_nav, TIER_COLORS
from pipeline.data_pipeline import get_data_pipeline
from pipeline.config import CHARGE_TYPE_LABELS, is_pace_model_ready

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="PACE — Upload",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

# ── Auth guard ────────────────────────────────────────────────────
require_auth()
username = st.session_state.get("username", "User")
top_nav(username)

# ── Model availability check ──────────────────────────────────────
MODEL_READY = is_pace_model_ready()

# ── Helper: tier color ────────────────────────────────────────────
def tier_badge(label: str) -> str:
    color = TIER_COLORS.get(label, "#94A3B8")
    return (
        f"<span style='background:rgba(0,0,0,0.3);border:1px solid {color};"
        f"color:{color};border-radius:4px;padding:2px 8px;"
        f"font-size:11px;font-weight:600;'>{label}</span>"
    )

# ── Schema badge ──────────────────────────────────────────────────
SCHEMA_LABELS = {
    "pace":           ("PACE Schema",     "#A78BFA"),
    "pace_aliased":   ("PACE (mapped)",   "#60A5FA"),
    "pace_converted": ("Legacy → PACE",   "#FCD34D"),
    "legacy":         ("Legacy Schema",   "#FB923C"),
    "unknown":        ("Unknown Schema",  "#F87171"),
}

# ── Page header ───────────────────────────────────────────────────
st.markdown("## Upload & Batch Score")
st.caption("Upload a CSV or Excel file to validate, clean, and score with the PACE model.")

if not MODEL_READY:
    st.info(
        "The PACE model is not yet trained. Uploads will be validated and "
        "processed — scoring will be available once training is complete.",
        icon="ℹ️"
    )

# ── File requirements expander ────────────────────────────────────
with st.expander("📋 Accepted Formats & Columns", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**PACE Schema (full)**
- `dot_number` — USDOT carrier number
- `oos_total`, `driver_oos_total`, `vehicle_oos_total`
- `basic_viol`, `unsafe_viol`, `vh_maint_viol`
- `crash_count`, `crash_avg_severity`
- All 152 FMCSA/EIA/FRED/weather columns

**Legacy Schema (auto-converted)**
- `shipment_id`, `ship_date`
- `carrier`, `facility`
- `weight_lbs`, `miles`
- `base_freight_usd`, `accessorial_charge_usd`
        """)
    with col_b:
        st.markdown("""
**Column aliases are auto-mapped**, for example:
- `dot` → `dot_number`
- `crashes` → `crash_count`
- `oos` → `oos_total`
- `carrier_state` → `carrier_phy_state`
- `diesel_price` → `eia_diesel_national`

**Accepted files:** `.csv`, `.xlsx`, `.xls`
**Max size:** 50 MB
        """)

st.divider()

# ── Upload zone ───────────────────────────────────────────────────
up_col, sample_col = st.columns([3, 1], gap="large")

with up_col:
    uploaded_file = st.file_uploader(
        "Drag & drop your file here, or click to browse",
        type=["csv", "xlsx", "xls"],
        help="Accepted: CSV, Excel · Max 50 MB",
    )

with sample_col:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    use_sample = st.button("Use sample data", type="secondary", use_container_width=True)
    st.caption("Loads 50 rows of mock PACE data")

# ── Load sample ───────────────────────────────────────────────────
if use_sample:
    from utils.mock_data import generate_mock_shipments
    sample = generate_mock_shipments(50)
    sample = sample.drop(
        columns=["risk_score", "risk_tier", "accessorial_type"], errors="ignore"
    )
    st.session_state["upload_raw_df"]      = sample
    st.session_state["upload_result"]      = None
    st.session_state["upload_scored"]      = None
    st.rerun()

# ── Parse uploaded file ───────────────────────────────────────────
if uploaded_file is not None:
    try:
        raw_df = parse_uploaded_document(uploaded_file, uploaded_file.name)
        if raw_df.empty:
            st.error("Uploaded file contains no usable data.")
        else:
            st.session_state["upload_raw_df"] = raw_df
            st.session_state["upload_result"] = None
            st.session_state["upload_scored"] = None
    except Exception as e:
        st.error(f"Could not parse file: {e}")

# ── Main processing ───────────────────────────────────────────────
if st.session_state.get("upload_raw_df") is not None:
    raw_df   = st.session_state["upload_raw_df"]
    pipeline = get_data_pipeline()

    # Run pipeline if not already done
    if st.session_state.get("upload_result") is None:
        with st.spinner("Analyzing file..."):
            result = pipeline.process_csv(raw_df)
            st.session_state["upload_result"] = result

    result       = st.session_state["upload_result"]
    errs         = result["errors"]
    warns        = result["warnings"]
    pass_count   = result["pass_count"]
    fail_count   = result["fail_count"]
    schema       = result["schema"]
    mapping      = result["mapping"]
    df_clean     = result["df_clean"]
    row_fail_mask = result["row_fail_mask"]

    schema_label, schema_color = SCHEMA_LABELS.get(schema, ("Unknown", "#F87171"))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Validation summary ────────────────────────────────────────
    with st.container(border=True):
        hdr_left, hdr_right = st.columns([3, 1])
        with hdr_left:
            st.markdown("#### Validation Results")
        with hdr_right:
            st.markdown(
                f"<div style='text-align:right;padding-top:4px;'>"
                f"<span style='background:rgba(0,0,0,0.3);border:1px solid {schema_color};"
                f"color:{schema_color};border-radius:4px;padding:3px 10px;"
                f"font-size:12px;font-weight:600;'>{schema_label}</span></div>",
                unsafe_allow_html=True,
            )

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("Total Rows", f"{len(raw_df):,}")
        with s2:
            st.metric("✅ Passed", f"{pass_count:,}")
        with s3:
            st.metric("❌ Failed", f"{fail_count:,}")
        with s4:
            st.metric("⚠️ Warnings", f"{len(warns)}")

        st.divider()

        if not errs and not warns:
            st.success("All rows passed validation — ready to score.")

        # Column mapping report
        if mapping:
            with st.expander(f"🔀 Column Aliases Applied ({len(mapping)})", expanded=False):
                alias_df = pd.DataFrame(
                    [(orig, canon) for orig, canon in mapping.items()],
                    columns=["Original Column", "Mapped To"]
                )
                st.dataframe(alias_df, hide_index=True, use_container_width=True)

        # Schema conversion note
        if schema == "pace_converted":
            st.info(
                "Legacy schema detected and auto-converted to PACE format. "
                "Some features were approximated from available columns. "
                "For best accuracy, use the full PACE schema with DOT numbers.",
                icon="🔄"
            )

        if errs:
            with st.expander(f"❌ Errors ({len(errs)})", expanded=True):
                for e in errs[:50]:
                    st.markdown(
                        f"<p style='margin:4px 0;font-size:13px;color:#F87171;'>• {e}</p>",
                        unsafe_allow_html=True,
                    )
                if len(errs) > 50:
                    st.caption(f"… and {len(errs) - 50} more errors.")

        if warns:
            with st.expander(f"⚠️ Warnings ({len(warns)})", expanded=False):
                for w in warns[:50]:
                    st.markdown(
                        f"<p style='margin:4px 0;font-size:13px;color:#FCD34D;'>• {w}</p>",
                        unsafe_allow_html=True,
                    )
                if len(warns) > 50:
                    st.caption(f"… and {len(warns) - 50} more warnings.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Data preview + score button ───────────────────────────────
    with st.container(border=True):
        hdr_col, btn_col = st.columns([4, 1])

        with hdr_col:
            st.markdown(f"#### Data Preview — first {min(25, len(raw_df))} rows")

        with btn_col:
            score_clicked = st.button(
                "Score with PACE →",
                type="primary",
                disabled=bool(errs) or (pass_count == 0) or not MODEL_READY,
                use_container_width=True,
            )

        if errs:
            st.caption("⚠️ Resolve all errors before scoring.")
        elif not MODEL_READY:
            st.caption("⏳ Model training in progress — scoring available soon.")

        # Show scored or raw preview
        scored = st.session_state.get("upload_scored")
        preview = scored.head(25) if scored is not None else raw_df.head(25)

        col_config = {}
        if scored is not None and "risk_score_pct" in preview.columns:
            col_config["risk_score_pct"] = st.column_config.ProgressColumn(
                "Risk Score",
                format="%.0f%%",
                min_value=0,
                max_value=100,
            )

        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
            column_config=col_config,
        )

        # ── Run scoring ───────────────────────────────────────────
        if score_clicked and not errs and MODEL_READY:
            try:
                from pipeline.inference import get_inference_engine
                engine = get_inference_engine()

                with st.spinner(f"Scoring {pass_count:,} rows with PACE model..."):
                    scored_df = engine.predict_csv(
                        filepath=None,
                        output_path=None,
                    )
                    # predict_dataframe used here since df_clean is already processed
                    results_df = engine.predict_dataframe(df_clean)

                    # Combine with original identifiers
                    id_cols = [c for c in ["unique_id", "dot_number"]
                               if c in df_clean.columns]
                    if id_cols:
                        scored_df = pd.concat(
                            [df_clean[id_cols].reset_index(drop=True),
                             results_df.reset_index(drop=True)],
                            axis=1
                        )
                    else:
                        scored_df = results_df

                st.session_state["upload_scored"] = scored_df
                st.success(
                    f"✅ Scoring complete — {len(scored_df):,} rows scored."
                )
                st.rerun()

            except Exception as e:
                st.error(f"Scoring failed: {e}")

    # ── Results section (shown after scoring) ─────────────────────
    if st.session_state.get("upload_scored") is not None:
        scored = st.session_state["upload_scored"]
        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### Score Summary")

            if "charge_type" in scored.columns and "risk_score_pct" in scored.columns:
                # Metrics row
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    avg_risk = scored["risk_score_pct"].mean()
                    st.metric("Avg Risk Score", f"{avg_risk:.1f}%")
                with m2:
                    high_risk = (scored["risk_score_pct"] >= 75).sum()
                    st.metric("Critical Risk", f"{high_risk:,}")
                with m3:
                    top_charge = scored["charge_type"].value_counts().index[0]
                    st.metric("Top Charge Type", top_charge)
                with m4:
                    no_charge = (scored["charge_type"] == "No Charge").sum()
                    st.metric("No Charge", f"{no_charge:,}")

                st.markdown("<br>", unsafe_allow_html=True)

                chart_col, dist_col = st.columns(2)

                with chart_col:
                    # Charge type distribution
                    ct_counts = scored["charge_type"].value_counts()
                    fig_ct = go.Figure(go.Bar(
                        x=ct_counts.index.tolist(),
                        y=ct_counts.values.tolist(),
                        marker_color="#9333EA",
                        text=ct_counts.values.tolist(),
                        textposition="outside",
                        textfont={"color": "#E2E8F0"},
                    ))
                    fig_ct.update_layout(
                        title="Charge Type Distribution",
                        margin=dict(l=0, r=0, t=40, b=0), height=280,
                        plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
                        font=dict(color="#A78BFA"),
                        xaxis=dict(color="#94A3B8",
                                   gridcolor="rgba(150,50,200,0.15)"),
                        yaxis=dict(color="#94A3B8",
                                   gridcolor="rgba(150,50,200,0.15)"),
                    )
                    st.plotly_chart(fig_ct, use_container_width=True)

                with dist_col:
                    # Risk score histogram
                    fig_hist = go.Figure(go.Histogram(
                        x=scored["risk_score_pct"],
                        nbinsx=20,
                        marker_color="#6D28D9",
                        marker_line_color="#9333EA",
                        marker_line_width=1,
                    ))
                    fig_hist.add_vline(
                        x=avg_risk, line_dash="dash",
                        line_color="#F87171", line_width=2,
                        annotation_text=f"Avg: {avg_risk:.1f}%",
                        annotation_font_color="#F87171",
                    )
                    fig_hist.update_layout(
                        title="Risk Score Distribution",
                        margin=dict(l=0, r=0, t=40, b=0), height=280,
                        plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
                        font=dict(color="#A78BFA"),
                        xaxis=dict(title="Risk Score (%)", color="#94A3B8",
                                   gridcolor="rgba(150,50,200,0.15)"),
                        yaxis=dict(title="Count", color="#94A3B8",
                                   gridcolor="rgba(150,50,200,0.15)"),
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

            # ── Download results ──────────────────────────────────
            st.divider()
            dl_col1, dl_col2 = st.columns(2)

            with dl_col1:
                csv_buf = io.StringIO()
                scored.to_csv(csv_buf, index=False)
                st.download_button(
                    label="⬇️ Download Results CSV",
                    data=csv_buf.getvalue(),
                    file_name="pace_scored_results.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with dl_col2:
                if st.button("🔄 Clear & Upload New File",
                             use_container_width=True):
                    for key in ["upload_raw_df", "upload_result",
                                "upload_scored"]:
                        st.session_state.pop(key, None)
                    st.rerun()