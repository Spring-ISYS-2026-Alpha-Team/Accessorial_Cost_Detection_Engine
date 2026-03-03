# File: app.py

import os
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd
import pyodbc
import streamlit as st
from dotenv import load_dotenv
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from auth_utils import logout

# Load environment variables from .env file
load_dotenv()

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="PACE Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)

# -----------------------------
# Session State Initialization
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "username" not in st.session_state:
    st.session_state["username"] = "Unknown"

if "db_error" not in st.session_state:
    st.session_state["db_error"] = None

if "uploaded_df" not in st.session_state:
    st.session_state["uploaded_df"] = None

if "scored_df" not in st.session_state:
    st.session_state["scored_df"] = None

if "model" not in st.session_state:
    st.session_state["model"] = None


# -----------------------------
# Authentication (Mock)
# -----------------------------
def render_login() -> None:
    st.title("🔒 PACE Secure Login")
    st.markdown("Please authenticate to access shipment data.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if username and password:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Please enter both username and password.")


if not st.session_state["authenticated"]:
    render_login()
    st.stop()


# -----------------------------
# Sidebar Navigation
# -----------------------------
with st.sidebar:
    st.title("PACE Navigation")
    st.write(f"👤 User: **{st.session_state.get('username', 'Unknown')}**")
    st.divider()

    if st.button("🔒 Log Out Securely", use_container_width=True, type="secondary"):
        logout()

    st.divider()
    st.info("Session Active ✅")


# -----------------------------
# Database Functions (Azure SQL)
# -----------------------------
@st.cache_resource
def get_connection():
    """
    Create a cached SQL Server connection using credentials from .env.
    Azure SQL typically requires encryption options.
    """
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")

    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )

    try:
        conn = pyodbc.connect(conn_str, timeout=10)
        st.session_state["db_error"] = None
        return conn
    except Exception as e:
        st.session_state["db_error"] = str(e)
        return None


@st.cache_data
def get_tables(_conn) -> List[str]:
    """Fetch all base table names from the database."""
    if _conn is None:
        return []

    query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """
    try:
        return pd.read_sql(query, _conn)["TABLE_NAME"].tolist()
    except Exception:
        return []


@st.cache_data
def get_table_data(_conn, table_name: str, row_limit: int) -> pd.DataFrame:
    """Fetch up to row_limit rows from the selected table."""
    if _conn is None:
        return pd.DataFrame()

    query = f"SELECT TOP {row_limit} * FROM [{table_name}]"
    try:
        return pd.read_sql(query, _conn)
    except Exception:
        return pd.DataFrame()


# -----------------------------
# Validation Rules
# -----------------------------
@dataclass(frozen=True)
class ValidationConfig:
    required_columns: Tuple[str, ...] = (
        "shipment_id",
        "ship_date",
        "carrier",
        "facility",
        "risk_tier",
        "weight_lbs",
        "miles",
        "base_freight_usd",
        "accessorial_charge_usd",
    )
    allowed_risk_tiers: Tuple[str, ...] = ("Low", "Medium", "High")
    weight_range: Tuple[float, float] = (0.0, 200000.0)
    miles_range: Tuple[float, float] = (0.0, 5000.0)
    money_range: Tuple[float, float] = (0.0, 1_000_000.0)


CFG = ValidationConfig()


def validate_shipments_df(df: pd.DataFrame, cfg: ValidationConfig) -> Tuple[bool, List[str], pd.DataFrame]:
    """
    Returns:
      - is_valid (bool)
      - errors (list[str])
      - cleaned_df (DataFrame) parsed/coerced as much as possible
    """
    errors: List[str] = []
    cleaned = df.copy()

    # 1) Required columns
    missing = [c for c in cfg.required_columns if c not in cleaned.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors, cleaned

    # 2) Coerce types
    cleaned["shipment_id"] = cleaned["shipment_id"].astype(str)
    cleaned["ship_date"] = pd.to_datetime(cleaned["ship_date"], errors="coerce")

    for col in ["carrier", "facility", "risk_tier"]:
        cleaned[col] = cleaned[col].astype(str).replace({"nan": np.nan, "None": np.nan})

    for col in ["weight_lbs", "miles", "base_freight_usd", "accessorial_charge_usd"]:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    # 3) Null checks
    required_non_null = ["shipment_id", "ship_date", "carrier", "facility", "risk_tier"]
    for col in required_non_null:
        null_count = int(cleaned[col].isna().sum())
        if null_count > 0:
            errors.append(f"Column '{col}' has {null_count} null/invalid value(s).")

    # 4) Allowed values
    invalid_risk = cleaned.loc[
        ~cleaned["risk_tier"].isin(cfg.allowed_risk_tiers) & cleaned["risk_tier"].notna(),
        "risk_tier",
    ]
    if not invalid_risk.empty:
        sample = ", ".join(sorted(set(invalid_risk.astype(str).head(5).tolist())))
        errors.append(
            f"Invalid risk_tier value(s). Allowed: {cfg.allowed_risk_tiers}. Found (sample): {sample}"
        )

    # 5) Range checks
    def range_check(col: str, lo: float, hi: float) -> None:
        bad = cleaned[col].notna() & ((cleaned[col] < lo) | (cleaned[col] > hi))
        bad_count = int(bad.sum())
        if bad_count > 0:
            errors.append(f"Column '{col}' has {bad_count} out-of-range value(s). Expected [{lo}, {hi}].")

    range_check("weight_lbs", *cfg.weight_range)
    range_check("miles", *cfg.miles_range)
    range_check("base_freight_usd", *cfg.money_range)
    range_check("accessorial_charge_usd", *cfg.money_range)

    return (len(errors) == 0), errors, cleaned


# -----------------------------
# Target + Feature Engineering + Model
# -----------------------------
def add_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Target definition:
      accessorial_occurred = 1 if accessorial_charge_usd > 0 else 0
    """
    out = df.copy()
    out["accessorial_occurred"] = (out["accessorial_charge_usd"].fillna(0) > 0).astype(int)
    return out


def build_model_pipeline() -> Pipeline:
    """
    Baseline logistic regression model.
    - OneHotEncode categorical
    - Impute missing numeric/categorical
    """
    categorical_features = ["carrier", "facility", "risk_tier"]
    numeric_features = ["weight_lbs", "miles", "base_freight_usd"]

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", categorical_transformer, categorical_features),
            ("num", numeric_transformer, numeric_features),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )
    return model


def train_baseline_on_synthetic() -> Pipeline:
    """
    Trains a baseline model on synthetic data so the app can score uploads
    even before the real database is ready.
    """
    rng = np.random.default_rng(42)
    n = 2000

    carriers = np.array(["UPS", "FedEx", "XPO", "JBT"])
    facilities = np.array(["DAL1", "MEM2", "CHI3", "LIT4"])
    tiers = np.array(["Low", "Medium", "High"])

    df = pd.DataFrame(
        {
            "shipment_id": [f"SYN{i}" for i in range(n)],
            "ship_date": pd.date_range("2025-01-01", periods=n, freq="h"),
            "carrier": rng.choice(carriers, size=n),
            "facility": rng.choice(facilities, size=n),
            "risk_tier": rng.choice(tiers, size=n, p=[0.55, 0.30, 0.15]),
            "weight_lbs": rng.normal(20000, 8000, size=n).clip(0, 200000),
            "miles": rng.normal(700, 300, size=n).clip(0, 5000),
            "base_freight_usd": rng.normal(1800, 700, size=n).clip(0, 1_000_000),
        }
    )

    tier_score = df["risk_tier"].map({"Low": 0.2, "Medium": 0.5, "High": 0.8}).astype(float)
    prob = (0.15 + 0.5 * tier_score + 0.00002 * df["miles"] + 0.0000005 * df["weight_lbs"]).clip(0, 0.95)

    occurred = (rng.random(n) < prob).astype(int)
    df["accessorial_charge_usd"] = occurred * rng.gamma(shape=2.0, scale=150.0, size=n)

    df = add_target(df)

    X = df[["carrier", "facility", "risk_tier", "weight_lbs", "miles", "base_freight_usd"]]
    y = df["accessorial_occurred"]

    pipeline = build_model_pipeline()
    pipeline.fit(X, y)
    return pipeline


def score_shipments(df: pd.DataFrame, model: Pipeline) -> pd.DataFrame:
    out = df.copy()
    X = out[["carrier", "facility", "risk_tier", "weight_lbs", "miles", "base_freight_usd"]]
    proba = model.predict_proba(X)[:, 1]
    out["risk_score"] = proba
    out["risk_tier_model"] = pd.cut(
        out["risk_score"],
        bins=[-0.001, 0.33, 0.66, 1.001],
        labels=["Low", "Medium", "High"],
    )
    return out


# -----------------------------
# Main UI
# -----------------------------
st.title("PACE — Predictive Accessorial Cost Detection Engine")
st.caption("CSV Upload • Validation • Scoring • Dashboard")

# Ensure baseline model exists
if st.session_state["model"] is None:
    st.session_state["model"] = train_baseline_on_synthetic()

# -----------------------------
# CSV Upload
# -----------------------------
st.subheader("Upload Shipments CSV")
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file)

        if df_upload.empty:
            st.warning("Uploaded file is empty.")
        else:
            st.success("File uploaded successfully.")
            st.caption(f"{len(df_upload):,} rows × {len(df_upload.columns):,} columns")
            st.dataframe(df_upload.head(25), use_container_width=True, hide_index=True)

            is_valid, errors, cleaned = validate_shipments_df(df_upload, CFG)

            if not is_valid:
                st.error("Validation failed. Please fix the issues below and re-upload.")
                for msg in errors:
                    st.write(f"- {msg}")
                st.session_state["uploaded_df"] = None
                st.session_state["scored_df"] = None
            else:
                st.success("Validation passed.")
                cleaned = add_target(cleaned)
                scored = score_shipments(cleaned, st.session_state["model"])

                st.session_state["uploaded_df"] = cleaned
                st.session_state["scored_df"] = scored

                st.subheader("Scored Results Preview")
                st.dataframe(scored.head(50), use_container_width=True, hide_index=True)

    except pd.errors.ParserError:
        st.error("Malformed CSV file. Please check delimiter and file format.")
    except UnicodeDecodeError:
        st.error("File encoding error. Please upload a UTF-8 encoded CSV.")
    except Exception as e:
        st.error(f"Unexpected error while reading file: {e}")

st.divider()

# -----------------------------
# Filters + Dashboard
# -----------------------------
st.subheader("Dashboard")

df_dashboard = st.session_state.get("scored_df")
if df_dashboard is None or df_dashboard.empty:
    st.info("Upload a valid CSV to see dashboard metrics and filters.")
else:
    with st.sidebar:
        st.header("Filters")

        min_date = df_dashboard["ship_date"].min()
        max_date = df_dashboard["ship_date"].max()

        date_range = st.date_input(
            "Ship Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
        )

        carriers = sorted(df_dashboard["carrier"].dropna().unique().tolist())
        selected_carriers = st.multiselect("Carrier", carriers, default=carriers)

        facilities = sorted(df_dashboard["facility"].dropna().unique().tolist())
        selected_facilities = st.multiselect("Facility", facilities, default=facilities)

        tiers = ["Low", "Medium", "High"]
        selected_tiers = st.multiselect("Risk Tier (Model)", tiers, default=tiers)

    start_date, end_date = date_range
    mask = (
        (df_dashboard["ship_date"].dt.date >= start_date)
        & (df_dashboard["ship_date"].dt.date <= end_date)
        & (df_dashboard["carrier"].isin(selected_carriers))
        & (df_dashboard["facility"].isin(selected_facilities))
        & (df_dashboard["risk_tier_model"].isin(selected_tiers))
    )
    df_filtered = df_dashboard.loc[mask].copy()

    c1, c2, c3 = st.columns(3)
    c1.metric("Shipments", f"{len(df_filtered):,}")
    c2.metric("Avg Risk Score", f"{df_filtered['risk_score'].mean():.3f}")
    c3.metric("Predicted High Risk", f"{int((df_filtered['risk_tier_model'] == 'High').sum()):,}")

    st.caption(f"Filtered: {len(df_filtered):,} rows × {len(df_filtered.columns):,} columns")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

st.divider()

# -----------------------------
# Database Viewer (Azure SQL)
# -----------------------------
st.subheader("Database Viewer (Azure SQL)")
st.caption("This section will work once valid .env SQL Server credentials are provided.")

conn = get_connection()
if conn is not None:
    with st.sidebar:
        st.header("DB Table Viewer")
        tables = get_tables(conn)

        if not tables:
            st.warning("No tables found in the database.")
            selected_table = None
            row_limit = 500
        else:
            selected_table = st.selectbox("Select DB Table", tables)
            row_limit = st.slider(
                "DB Row Limit",
                min_value=100,
                max_value=5000,
                value=500,
                step=100,
            )

    if tables and selected_table:
        st.subheader(f"DB Table: `{selected_table}`")
        df_db = get_table_data(conn, selected_table, row_limit)
        st.caption(f"Showing {len(df_db):,} rows × {len(df_db.columns):,} columns")
        st.dataframe(df_db, use_container_width=True, hide_index=True)
else:
    st.warning("Database connection is not available.")
    with st.expander("Show database error details"):
        st.code(st.session_state.get("db_error") or "No error details available.")