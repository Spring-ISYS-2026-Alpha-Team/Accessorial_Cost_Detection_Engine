import os
import sys

import numpy as np
import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.doc_parser import parse_uploaded_document
from utils.styling import NAVY_900, inject_css, top_nav  # noqa: F401

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
    "shipment_id",
    "ship_date",
    "carrier",
    "facility",
    "weight_lbs",
    "miles",
    "base_freight_usd",
    "accessorial_charge_usd",
]


def validate_dataframe(df: pd.DataFrame):
    """
    Returns:
      errors:   list[str]
      warnings: list[str]
      row_fail_mask: boolean Series (True if row has ANY error)
    """
    errors = []
    warnings = []

    # 1) Required columns
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        errors.append(f"Missing required column(s): {', '.join(missing)}")
        return errors, warnings, None

    # 2) Normalize / coerce types (vectorized)
    out = df.copy()

    # shipment_id / carrier / facility required and non-empty
    for col in ["shipment_id", "carrier", "facility"]:
        out[col] = out[col].astype(str)

    empty_text = (
        (out["shipment_id"].str.strip() == "")
        | (out["carrier"].str.strip() == "")
        | (out["facility"].str.strip() == "")
    )

    # dates
    ship_dt = pd.to_datetime(out["ship_date"], errors="coerce")
    bad_date = ship_dt.isna()

    # numerics
    weight = pd.to_numeric(out["weight_lbs"], errors="coerce")
    miles = pd.to_numeric(out["miles"], errors="coerce")
    base = pd.to_numeric(out["base_freight_usd"], errors="coerce")
    acc = pd.to_numeric(out["accessorial_charge_usd"], errors="coerce")

    bad_weight_type = weight.isna()
    bad_miles_type = miles.isna()
    bad_base_type = base.isna()
    bad_acc_type = acc.isna()

    bad_weight_range = ~(weight.between(0, 200_000, inclusive="both"))
    bad_miles_range = ~(miles.between(0, 5_000, inclusive="both"))
    bad_base_neg = base < 0
    bad_acc_neg = acc < 0

    # Row has ANY error
    row_fail_mask = (
        empty_text
        | bad_date
        | bad_weight_type
        | bad_miles_type
        | bad_base_type
        | bad_acc_type
        | bad_weight_range
        | bad_miles_range
        | bad_base_neg
        | bad_acc_neg
    )

    # 3) Build human-readable messages
    MAX_MSG = 200

    def add_row_msgs(mask: pd.Series, msg_fn):
        nonlocal errors
        idxs = mask[mask].index.tolist()
        for idx in idxs[:MAX_MSG]:
            errors.append(msg_fn(idx + 2, df.loc[idx]))
        if len(idxs) > MAX_MSG:
            errors.append(f"… and {len(idxs) - MAX_MSG} more similar errors.")

    if empty_text.any():
        add_row_msgs(
            empty_text,
            lambda row_num, r: f"Row {row_num}: 'shipment_id', 'carrier', or 'facility' is empty/missing.",
        )

    if bad_date.any():
        add_row_msgs(
            bad_date,
            lambda row_num, r: f"Row {row_num}: 'ship_date' value '{r['ship_date']}' is not a valid date.",
        )

    if bad_weight_type.any():
        add_row_msgs(
            bad_weight_type,
            lambda row_num, r: f"Row {row_num}: 'weight_lbs' is not a number.",
        )

    if bad_miles_type.any():
        add_row_msgs(
            bad_miles_type,
            lambda row_num, r: f"Row {row_num}: 'miles' is not a number.",
        )

    if bad_base_type.any():
        add_row_msgs(
            bad_base_type,
            lambda row_num, r: f"Row {row_num}: 'base_freight_usd' is not a number.",
        )

    if bad_acc_type.any():
        add_row_msgs(
            bad_acc_type,
            lambda row_num, r: f"Row {row_num}: 'accessorial_charge_usd' is not a number.",
        )

    if (bad_weight_range & ~bad_weight_type).any():
        add_row_msgs(
            bad_weight_range & ~bad_weight_type,
            lambda row_num, r: f"Row {row_num}: 'weight_lbs' is out of range (0–200,000).",
        )

    if (bad_miles_range & ~bad_miles_type).any():
        add_row_msgs(
            bad_miles_range & ~bad_miles_type,
            lambda row_num, r: f"Row {row_num}: 'miles' is out of range (0–5,000).",
        )

    if (bad_base_neg & ~bad_base_type).any():
        add_row_msgs(
            bad_base_neg & ~bad_base_type,
            lambda row_num, r: f"Row {row_num}: 'base_freight_usd' cannot be negative.",
        )

    if (bad_acc_neg & ~bad_acc_type).any():
        add_row_msgs(
            bad_acc_neg & ~bad_acc_type,
            lambda row_num, r: f"Row {row_num}: 'accessorial_charge_usd' cannot be negative.",
        )

    blank_acc = df["accessorial_charge_usd"].isna() | (
        df["accessorial_charge_usd"].astype(str).str.strip() == ""
    )
    warn_idxs = blank_acc[blank_acc].index.tolist()
    for idx in warn_idxs[:MAX_MSG]:
        warnings.append(
            f"Row {idx + 2}: 'accessorial_charge_usd' is blank — defaulted to 0."
        )
    if len(warn_idxs) > MAX_MSG:
        warnings.append(f"… and {len(warn_idxs) - MAX_MSG} more similar warnings.")

    return errors, warnings, row_fail_mask


def mock_score(df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(99)
    scored = df.copy()

    scored["weight_lbs"] = pd.to_numeric(scored["weight_lbs"], errors="coerce").fillna(0)
    scored["miles"] = pd.to_numeric(scored["miles"], errors="coerce").fillna(0)
    scored["base_freight_usd"] = pd.to_numeric(
        scored["base_freight_usd"], errors="coerce"
    ).fillna(0)

    w_norm = scored["weight_lbs"] / 44_000
    m_norm = scored["miles"] / 5_000
    noise = rng.uniform(0, 0.2, len(scored))

    scored["risk_score"] = np.clip((w_norm * 0.3 + m_norm * 0.4 + noise), 0.05, 0.98).round(3)
    scored["risk_tier"] = scored["risk_score"].apply(
        lambda x: "High" if x >= 0.67 else "Medium" if x >= 0.34 else "Low"
    )

    return scored


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("## Upload Shipment Data")
st.caption("Upload a shipment file to validate your data and generate risk predictions.")

with st.expander("📋 File Requirements", expanded=False):
    st.markdown(
        """
**Required columns:**
- `shipment_id`
- `ship_date` *(YYYY-MM-DD)*
- `carrier`
- `facility`
- `weight_lbs` *(0 – 200,000)*
- `miles` *(0 – 5,000)*
- `base_freight_usd` *(≥ 0)*
- `accessorial_charge_usd` *(≥ 0)*

**Accepted files:** `.csv`, `.xlsx`, `.xls`, `.pdf`, `.png`, `.jpg`, `.jpeg`  
**Max size:** 10 MB
        """
    )

st.divider()

# ── Upload zone ───────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drag & drop your file here, or click to browse",
    type=["csv", "xlsx", "xls", "pdf", "png", "jpg", "jpeg"],
    help="Accepted formats: CSV, Excel, PDF, Image · Max size: 10 MB",
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
    st.session_state["upload_df"] = sample.drop(
        columns=["risk_score", "risk_tier", "accessorial_type"],
        errors="ignore",
    )
    st.session_state["upload_scored"] = None
    st.session_state["upload_errors"] = []
    st.session_state["upload_warnings"] = []
    st.session_state["upload_row_fail_mask"] = None
    st.rerun()

# ── Parse uploaded file ───────────────────────────────────────────────────────
if uploaded_file is not None:
    try:
        raw_df = parse_uploaded_document(uploaded_file, uploaded_file.name)

        if raw_df.empty:
            st.error("Uploaded file contains no usable data.")
        else:
            st.session_state["upload_df"] = raw_df
            st.session_state["upload_scored"] = None
            st.session_state["upload_errors"] = []
            st.session_state["upload_warnings"] = []
            st.session_state["upload_row_fail_mask"] = None

    except Exception as e:
        st.error(f"Could not parse file: {e}")

# ── Validation + results ──────────────────────────────────────────────────────
if st.session_state.get("upload_df") is not None:
    raw_df = st.session_state["upload_df"]

    if (
        st.session_state.get("upload_row_fail_mask") is None
        and not st.session_state.get("upload_errors")
    ):
        errs, warns, row_fail_mask = validate_dataframe(raw_df)
        st.session_state["upload_errors"] = errs
        st.session_state["upload_warnings"] = warns
        st.session_state["upload_row_fail_mask"] = row_fail_mask

    errs = st.session_state.get("upload_errors", [])
    warns = st.session_state.get("upload_warnings", [])
    row_fail_mask = st.session_state.get("upload_row_fail_mask")

    if row_fail_mask is None:
        pass_count = 0
        fail_count = len(raw_df)
    else:
        fail_count = int(row_fail_mask.sum())
        pass_count = int((~row_fail_mask).sum())

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Validation Results")

        s1, s2, s3 = st.columns(3)
        with s1:
            st.markdown(
                f"<div style='font-size:15px; font-weight:600; color:#059669;'>✅ {pass_count:,} rows passed</div>",
                unsafe_allow_html=True,
            )
        with s2:
            st.markdown(
                f"<div style='font-size:15px; font-weight:600; color:#D97706;'>⚠️ {len(warns)} warning{'s' if len(warns) != 1 else ''}</div>",
                unsafe_allow_html=True,
            )
        with s3:
            st.markdown(
                f"<div style='font-size:15px; font-weight:600; color:#DC2626;'>❌ {fail_count:,} rows failed</div>",
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
                    st.caption(f"… and {len(errs) - 50} more errors (see above summaries).")

        if warns:
            with st.expander(f"⚠️ Warnings ({len(warns)})", expanded=False):
                for w in warns[:50]:
                    st.markdown(
                        f"<p style='margin:4px 0; font-size:13px; color:#D97706;'>• {w}</p>",
                        unsafe_allow_html=True,
                    )
                if len(warns) > 50:
                    st.caption(f"… and {len(warns) - 50} more warnings.")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        hdr_col, btn_col = st.columns([4, 1])

        with hdr_col:
            st.markdown(f"#### Data Preview — first {min(25, len(raw_df))} rows")

        with btn_col:
            score_clicked = st.button(
                "Generate Risk Scores →",
                type="primary",
                disabled=bool(errs) or (pass_count == 0),
                width="stretch",
            )

        if errs:
            st.caption("⚠️ Resolve all errors before scoring.")

        preview = raw_df.head(25)
        if st.session_state.get("upload_scored") is not None:
            preview = st.session_state["upload_scored"].head(25)

        scored_cols = ["risk_score", "risk_tier"] if "risk_score" in preview.columns else []

        st.dataframe(
            preview,
            width="stretch",
            hide_index=True,
            column_config={
                "risk_score": st.column_config.ProgressColumn(
                    "Risk Score",
                    format="%.0f%%",
                    min_value=0,
                    max_value=1,
                )
            }
            if scored_cols
            else {},
        )

        if score_clicked and not errs:
            with st.spinner("Running risk scoring model…"):
                scored_df = mock_score(raw_df)
                st.session_state["upload_scored"] = scored_df

            st.success(
                f"Scoring complete! {len(scored_df):,} shipments scored. Results shown in preview above."
            )
            st.rerun()