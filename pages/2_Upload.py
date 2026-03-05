# File: pages/2_Upload.py
import streamlit as st
import pandas as pd
import numpy as np
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.styling import inject_css, top_nav, NAVY_900

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PACE — Upload",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

# ── Auth guard ────────────────────────────────────────────────────────────────
if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

# ── Validation helpers ────────────────────────────────────────────────────────
REQUIRED_COLS = [
    "shipment_id", "ship_date", "carrier", "facility",
    "weight_lbs", "miles", "base_freight_usd", "accessorial_charge_usd",
]

def validate_dataframe(df: pd.DataFrame):
    errors   = []
    warnings = []

    # 1. Required columns
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        errors.append(f"Missing required column(s): {', '.join(missing)}")
        return errors, warnings

    # 2. Row-level checks
    for idx, row in df.iterrows():
        row_num = idx + 2

        for col in ["shipment_id", "carrier", "facility"]:
            if pd.isnull(row[col]) or str(row[col]).strip() == "":
                errors.append(f"Row {row_num}: '{col}' is empty or missing.")

        try:
            pd.to_datetime(row["ship_date"])
        except Exception:
            errors.append(f"Row {row_num}: 'ship_date' value '{row['ship_date']}' is not a valid date.")

        try:
            w = float(row["weight_lbs"])
            if not (0 <= w <= 200_000):
                errors.append(f"Row {row_num}: 'weight_lbs' value {w:,.0f} is out of range (0–200,000).")
        except (ValueError, TypeError):
            errors.append(f"Row {row_num}: 'weight_lbs' is not a number.")

        try:
            m = float(row["miles"])
            if not (0 <= m <= 5_000):
                errors.append(f"Row {row_num}: 'miles' value {m:,.0f} is out of range (0–5,000).")
        except (ValueError, TypeError):
            errors.append(f"Row {row_num}: 'miles' is not a number.")

        try:
            bf = float(row["base_freight_usd"])
            if bf < 0:
                errors.append(f"Row {row_num}: 'base_freight_usd' cannot be negative.")
        except (ValueError, TypeError):
            errors.append(f"Row {row_num}: 'base_freight_usd' is not a number.")

        try:
            ac = float(row["accessorial_charge_usd"])
            if ac < 0:
                errors.append(f"Row {row_num}: 'accessorial_charge_usd' cannot be negative.")
        except (ValueError, TypeError):
            errors.append(f"Row {row_num}: 'accessorial_charge_usd' is not a number.")

        if pd.isnull(row.get("accessorial_charge_usd")) or str(row.get("accessorial_charge_usd")).strip() == "":
            warnings.append(f"Row {row_num}: 'accessorial_charge_usd' is blank — defaulted to 0.")

    return errors, warnings


def mock_score(df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(99)
    scored = df.copy()

    scored["weight_lbs"]       = pd.to_numeric(scored["weight_lbs"],       errors="coerce").fillna(0)
    scored["miles"]            = pd.to_numeric(scored["miles"],            errors="coerce").fillna(0)
    scored["base_freight_usd"] = pd.to_numeric(scored["base_freight_usd"], errors="coerce").fillna(0)

    w_norm = scored["weight_lbs"] / 44_000
    m_norm = scored["miles"]      /  5_000
    noise  = rng.uniform(0, 0.2, len(scored))

    scored["risk_score"] = np.clip((w_norm * 0.3 + m_norm * 0.4 + noise), 0.05, 0.98).round(3)
    scored["risk_tier"]  = scored["risk_score"].apply(
        lambda x: "High" if x >= 0.67 else "Medium" if x >= 0.34 else "Low"
    )
    return scored


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("## Upload Shipment Data")
st.caption("Upload a CSV file to validate your data and generate risk predictions.")

with st.expander("📋 CSV Requirements", expanded=False):
    st.markdown("""
**Required columns:**
- `shipment_id`
- `ship_date` *(YYYY-MM-DD)*
- `carrier`
- `facility`
- `weight_lbs` *(0 – 200,000)*
- `miles` *(0 – 5,000)*
- `base_freight_usd` *(≥ 0)*
- `accessorial_charge_usd` *(≥ 0)*

**File:** `.csv` · Max 10 MB
    """)

st.divider()

# ── Upload zone ───────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drag & drop your CSV here, or click to browse",
    type=["csv"],
    help="Accepted format: .csv · Max size: 10 MB",
)

st.markdown(
    "<div style='text-align:center; color:#9CA3AF; margin:8px 0; font-size:13px;'>— or —</div>",
    unsafe_allow_html=True,
)

use_sample = st.button("Use sample data", type="secondary")

# ── Load sample data into session if requested ────────────────────────────────
if use_sample:
    from utils.mock_data import generate_mock_shipments
    sample = generate_mock_shipments(50)
    st.session_state["upload_df"]      = sample.drop(
        columns=["risk_score", "risk_tier", "accessorial_type"], errors="ignore"
    )
    st.session_state["upload_scored"]  = None
    st.session_state["upload_errors"]  = []
    st.session_state["upload_warnings"] = []
    st.rerun()

# ── Parse uploaded file ───────────────────────────────────────────────────────
if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)
        st.session_state["upload_df"]      = raw_df
        st.session_state["upload_scored"]  = None
        st.session_state["upload_errors"]  = []
        st.session_state["upload_warnings"] = []
    except Exception as e:
        st.error(f"Could not parse file: {e}")

# ── Validation + results ──────────────────────────────────────────────────────
if "upload_df" in st.session_state and st.session_state["upload_df"] is not None:
    raw_df = st.session_state["upload_df"]

    if not st.session_state.get("upload_errors") and not st.session_state.get("upload_warnings"):
        errs, warns = validate_dataframe(raw_df)
        st.session_state["upload_errors"]   = errs
        st.session_state["upload_warnings"] = warns

    errs  = st.session_state.get("upload_errors",   [])
    warns = st.session_state.get("upload_warnings", [])
    pass_count = len(raw_df) - len(errs)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### Validation Results")

        s1, s2, s3 = st.columns(3)
        with s1:
            st.markdown(
                f"<div style='font-size:15px; font-weight:600; color:#059669;'>"
                f"✅ {pass_count:,} rows passed</div>",
                unsafe_allow_html=True,
            )
        with s2:
            st.markdown(
                f"<div style='font-size:15px; font-weight:600; color:#D97706;'>"
                f"⚠️ {len(warns)} warning{'s' if len(warns) != 1 else ''}</div>",
                unsafe_allow_html=True,
            )
        with s3:
            st.markdown(
                f"<div style='font-size:15px; font-weight:600; color:#DC2626;'>"
                f"❌ {len(errs)} error{'s' if len(errs) != 1 else ''}</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        if not errs and not warns:
            st.success("All rows passed validation — ready to score.")

        if errs:
            with st.expander(f"❌ Errors ({len(errs)})", expanded=True):
                for e in errs[:50]:
                    st.markdown(
                        f"<p style='margin:4px 0; font-size:13px; color:#DC2626;'>• {e}</p>",
                        unsafe_allow_html=True,
                    )
                if len(errs) > 50:
                    st.caption(f"… and {len(errs) - 50} more errors.")

        if warns:
            with st.expander(f"⚠️ Warnings ({len(warns)})", expanded=False):
                for w in warns[:50]:
                    st.markdown(
                        f"<p style='margin:4px 0; font-size:13px; color:#D97706;'>• {w}</p>",
                        unsafe_allow_html=True,
                    )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        hdr_col, btn_col = st.columns([4, 1])
        with hdr_col:
            st.markdown(f"#### Data Preview — first {min(25, len(raw_df))} rows")
        with btn_col:
            score_clicked = st.button(
                "Generate Risk Scores →",
                type="primary",
                disabled=bool(errs),
                use_container_width=True,
            )

        if errs:
            st.caption("⚠️ Resolve all errors before scoring.")

        preview = raw_df.head(25)
        if st.session_state.get("upload_scored") is not None:
            preview = st.session_state["upload_scored"].head(25)

        scored_cols = ["risk_score", "risk_tier"] if "risk_score" in preview.columns else []

        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
            column_config={
                "risk_score": st.column_config.ProgressColumn(
                    "Risk Score", format="%.0f%%", min_value=0, max_value=1
                )
            } if scored_cols else {},
        )

        if score_clicked and not errs:
            with st.spinner("Running risk scoring model…"):
                scored_df = mock_score(raw_df)
                st.session_state["upload_scored"] = scored_df
            st.success(
                f"Scoring complete! {len(scored_df):,} shipments scored. "
                "Results shown in preview above."
            )
            st.rerun()
