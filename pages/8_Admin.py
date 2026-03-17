# File: pages/8_Admin.py
import streamlit as st
<<<<<<< HEAD
import pandas as pd
from datetime import datetime
from typing import Optional
from textwrap import dedent

from auth_utils import check_auth, require_admin, show_user_info


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="PACE Admin Portal",
    page_icon="🛠️",
    layout="wide",
)

# =========================================================
# AUTH
# =========================================================
check_auth()
require_admin()

username = st.session_state.get("username", "Admin")
role = st.session_state.get("role", "admin")

# =========================================================
# TABLE NAMES
# =========================================================
USERS_TABLE = "PaceUsers"
SHIPMENTS_TABLE = "Shipments"
MODEL_TABLE = "ModelRegistry"
LOGS_TABLE = "AuditLogs"

# =========================================================
# DATABASE
# =========================================================
@st.cache_resource(show_spinner=False)
def get_db_connection():
    for fn_name in [
        "get_connection",
        "connect_to_db",
        "create_connection",
        "get_sql_connection",
    ]:
        try:
            import database
            fn = getattr(database, fn_name, None)
            if callable(fn):
                conn = fn()
                if conn is not None:
                    return conn
        except Exception:
            pass

    try:
        import pyodbc

        if "azure_sql" not in st.secrets:
            return None

        server = st.secrets["azure_sql"]["server"]
        database_name = st.secrets["azure_sql"]["database"]
        db_username = st.secrets["azure_sql"]["user"]
        password = st.secrets["azure_sql"]["password"]

        conn_str = (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server={server};"
            f"Database={database_name};"
            f"Uid={db_username};"
            f"Pwd={password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=15;"
        )
        return pyodbc.connect(conn_str)
    except Exception:
        return None


def has_db_connection() -> bool:
    try:
        return get_db_connection() is not None
    except Exception:
        return False


def run_select_query(query: str, params: Optional[tuple] = None) -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()

    try:
        if params is None:
            return pd.read_sql(query, conn)
        return pd.read_sql(query, conn, params=params)
    except Exception:
        return pd.DataFrame()


def run_action_query(query: str, params: Optional[tuple] = None) -> bool:
    conn = get_db_connection()
    if conn is None:
        st.warning("No database connection available.")
        return False

    try:
        cursor = conn.cursor()
        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        st.warning(f"Database action failed: {e}")
        return False


# =========================================================
# MOCK DATA
# =========================================================
def get_mock_users() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "user_id": 1,
                "full_name": "Admin User",
                "email": "admin@pace.local",
                "role": "Admin",
                "status": "Active",
                "department": "Operations",
                "created_at": "2026-02-01 09:00:00",
                "last_login": "2026-03-13 09:30:00",
                "failed_attempts": 0,
            },
            {
                "user_id": 2,
                "full_name": "Logistics Analyst",
                "email": "analyst@pace.local",
                "role": "Analyst",
                "status": "Active",
                "department": "Analytics",
                "created_at": "2026-02-05 10:15:00",
                "last_login": "2026-03-12 14:20:00",
                "failed_attempts": 1,
            },
            {
                "user_id": 3,
                "full_name": "Viewer User",
                "email": "viewer@pace.local",
                "role": "Viewer",
                "status": "Locked",
                "department": "Finance",
                "created_at": "2026-02-10 08:45:00",
                "last_login": None,
                "failed_attempts": 4,
            },
        ]
    )


def get_mock_shipments() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "shipment_id": 1001,
                "lane": "Dallas-Chicago",
                "carrier": "JB Hunt",
                "facility_type": "Grocery DC",
                "appointment_type": "Live",
                "base_freight_usd": 2400,
                "accessorial_charge_usd": 300,
                "risk_score": 82,
                "risk_level": "High",
                "validation_status": "Pending Review",
                "uploaded_by": "Admin",
                "uploaded_at": "2026-03-12 13:00:00",
            },
            {
                "shipment_id": 1002,
                "lane": "Memphis-Atlanta",
                "carrier": "Werner",
                "facility_type": "Manufacturing Plant",
                "appointment_type": "Drop",
                "base_freight_usd": 1800,
                "accessorial_charge_usd": 0,
                "risk_score": 41,
                "risk_level": "Medium",
                "validation_status": "Clean",
                "uploaded_by": "Admin",
                "uploaded_at": "2026-03-12 11:00:00",
            },
            {
                "shipment_id": 1003,
                "lane": "Little Rock-Houston",
                "carrier": "Swift",
                "facility_type": "Port",
                "appointment_type": "Live",
                "base_freight_usd": 2100,
                "accessorial_charge_usd": 120,
                "risk_score": 22,
                "risk_level": "Low",
                "validation_status": "Rejected",
                "uploaded_by": "Admin",
                "uploaded_at": "2026-03-11 15:45:00",
            },
        ]
    )


def get_mock_models() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "model_name": "PACE Logistic Regression",
                "version": "v1.0",
                "status": "Active",
                "accuracy": 0.78,
                "auc_roc": 0.74,
                "last_trained": "2026-03-10 21:00:00",
                "features": 24,
            },
            {
                "model_name": "PACE Random Forest",
                "version": "v1.1",
                "status": "Inactive",
                "accuracy": 0.81,
                "auc_roc": 0.79,
                "last_trained": "2026-03-09 22:10:00",
                "features": 31,
            },
        ]
    )


def get_mock_logs() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": "2026-03-13 09:40:00",
                "severity": "INFO",
                "module": "DB",
                "user_name": "Admin",
                "action": "Load admin portal",
                "details": "Admin portal opened successfully.",
            },
            {
                "timestamp": "2026-03-13 09:15:00",
                "severity": "WARN",
                "module": "DATA",
                "user_name": "Admin",
                "action": "Pending review",
                "details": "Shipment 1001 marked Pending Review.",
            },
            {
                "timestamp": "2026-03-12 18:20:00",
                "severity": "INFO",
                "module": "MODEL",
                "user_name": "Admin",
                "action": "Activate model",
                "details": "PACE Logistic Regression set as active model.",
            },
        ]
    )


# =========================================================
# SETTINGS
# =========================================================
def load_settings():
    if "admin_settings" not in st.session_state:
        st.session_state.admin_settings = {
            "high_risk_threshold": 70,
            "medium_risk_threshold": 40,
            "cost_alert_threshold": 500,
            "auto_lock_failed_attempts": 4,
            "allow_csv_upload": True,
            "allow_manual_entry": True,
            "maintenance_mode": False,
            "prediction_pipeline": True,
            "nightly_retraining": False,
            "db_status": "Connected" if has_db_connection() else "Offline / Mock Mode",
        }


# =========================================================
# LOGGING
# =========================================================
def add_log(severity: str, module: str, user_name: str, action: str, details: str):
    if has_db_connection():
        query = f"""
            INSERT INTO {LOGS_TABLE} (
                timestamp, severity, module, user_name, action, details
=======
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import get_connection, get_pace_users, create_pace_user, delete_pace_user
from utils.styling import inject_css, top_nav, ACCENT_SOFT, TEXT_PRIMARY, TEXT_SECONDARY
import utils.model_config as mcfg
from utils.risk_model import retrain, incremental_update, rollback_to_version, list_saved_versions, get_risk_model
from utils.mock_data import generate_mock_shipments

st.set_page_config(
    page_title="PACE — Admin",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

role = st.session_state.get("role", "user")
if role != "admin":
    st.error("Access denied. Admins only.")
    st.page_link("pages/0_Home.py", label="Go to Home", icon="🏠")
    st.stop()

username = st.session_state.get("username", "Admin")
top_nav(username)

conn = get_connection()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Admin Panel")
st.caption(f"Logged in as **{username}** · admin")
st.divider()

# ── User Management ───────────────────────────────────────────────────────────
col_form, col_users = st.columns([1, 2], gap="large")

with col_form:
    with st.container(border=True):
        st.markdown("#### Create User")
        with st.form("create_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["user", "admin"])
            submitted = st.form_submit_button("Create User", width="stretch", type="primary")
            if submitted:
                if not new_username or not new_password:
                    st.error("Username and password are required.")
                elif conn is None:
                    st.warning("No DB connection — cannot create user.")
                else:
                    ok, msg = create_pace_user(conn, new_username, new_password, new_role)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(f"Failed: {msg}")

with col_users:
    with st.container(border=True):
        st.markdown("#### Current Users")
        if conn is None:
            st.warning("No database connection — showing fallback accounts only.")
            st.dataframe(
                [{"username": "admin", "role": "admin"}, {"username": "user", "role": "user"}],
                width="stretch", hide_index=True,
            )
        else:
            users_df = get_pace_users(conn)
            if users_df.empty:
                st.info("No users found in PaceUsers table.")
            else:
                st.dataframe(users_df, width="stretch", hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("#### Delete User")
        if conn is not None:
            users_df2 = get_pace_users(conn)
            deletable = [u for u in users_df2["username"].tolist() if u != username] if not users_df2.empty else []
            if deletable:
                del_user = st.selectbox("Select user to delete", deletable, key="del_user_sel")
                if st.button("Delete User", type="primary"):
                    ok, msg = delete_pace_user(conn, del_user)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(f"Failed: {msg}")
            else:
                st.caption("No other users to delete.")
        else:
            st.caption("Database unavailable.")

st.divider()

# ── Model Management ───────────────────────────────────────────────────────────
st.markdown("## Model Management")
st.caption("Control how PACE learns from your data. All model activity stays within your deployment.")
st.markdown("<br>", unsafe_allow_html=True)

cfg = mcfg.load()

# ── Row 1: Status cards ────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4, gap="medium")

mode_color = "#9333EA" if cfg["mode"] == "production" else "#64748B"
mode_label = "PRODUCTION" if cfg["mode"] == "production" else "DEMO"

with c1:
    with st.container(border=True):
        st.markdown(f"<p style='color:{mode_color};font-size:11px;font-weight:700;letter-spacing:1px;margin:0'>{mode_label}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:22px;font-weight:700;margin:4px 0 0'>Model Mode</p>", unsafe_allow_html=True)
        st.caption("Demo uses mock data only")

with c2:
    with st.container(border=True):
        auc = cfg["metrics"].get("auc")
        auc_display = f"{auc:.2f}" if auc else "—"
        color = "#22C55E" if auc and auc >= 0.75 else "#F59E0B" if auc else "#64748B"
        st.markdown(f"<p style='color:{color};font-size:11px;font-weight:700;letter-spacing:1px;margin:0'>AUC SCORE</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:28px;font-weight:700;margin:4px 0 0'>{auc_display}</p>", unsafe_allow_html=True)
        st.caption("Model accuracy (0–1)")

with c3:
    with st.container(border=True):
        n = cfg.get("records_trained_on", 0)
        st.markdown(f"<p style='color:{ACCENT_SOFT};font-size:11px;font-weight:700;letter-spacing:1px;margin:0'>TRAINED ON</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:28px;font-weight:700;margin:4px 0 0'>{n:,}</p>", unsafe_allow_html=True)
        st.caption("Total shipment records")

with c4:
    with st.container(border=True):
        pending = cfg.get("pending_records", 0)
        p_color = "#22C55E" if pending >= cfg.get("auto_update_threshold", 100) else "#64748B"
        st.markdown(f"<p style='color:{p_color};font-size:11px;font-weight:700;letter-spacing:1px;margin:0'>PENDING</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:28px;font-weight:700;margin:4px 0 0'>{pending:,}</p>", unsafe_allow_html=True)
        st.caption(f"New records since last update (threshold: {cfg.get('auto_update_threshold', 100)})")

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 2: Controls + Version History ─────────────────────────────────────────
col_controls, col_versions = st.columns([1, 1], gap="large")

with col_controls:
    with st.container(border=True):
        st.markdown("#### Model Settings")

        # Mode toggle
        new_mode = st.selectbox(
            "Model mode",
            ["demo", "production"],
            index=0 if cfg["mode"] == "demo" else 1,
            help="Demo uses mock data. Production learns from your real uploaded shipments.",
        )
        if new_mode != cfg["mode"]:
            mcfg.set_mode(new_mode)
            st.success(f"Switched to {new_mode} mode.")
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Risk tier thresholds
        st.markdown("**Risk Tier Thresholds**")
        st.caption("Adjust what score counts as High or Medium risk for your operation.")

        suggested = cfg.get("suggested_thresholds", {})
        sug_high  = suggested.get("high")
        sug_med   = suggested.get("medium")

        high_thresh = st.slider(
            "High risk cutoff", 0.50, 0.95,
            float(cfg["tier_thresholds"]["high"]), 0.01,
            help="Shipments above this score are flagged High Risk",
        )
        if sug_high:
            diff_h = round(high_thresh - sug_high, 2)
            arrow  = "↑ above" if diff_h > 0 else "↓ below" if diff_h < 0 else "matches"
            color  = "#22C55E" if abs(diff_h) <= 0.05 else "#F59E0B"
            st.markdown(
                f"<p style='font-size:11px;color:{color};margin:-8px 0 8px;'>"
                f"📊 Data suggests <strong>{sug_high}</strong> &nbsp;·&nbsp; "
                f"current is {abs(diff_h):.2f} {arrow} recommendation</p>",
                unsafe_allow_html=True,
>>>>>>> f816b21e6a81e7f212cc77be2e2f8c04286bfdbf
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            severity,
            module,
            user_name,
            action,
            details,
        )
        run_action_query(query, params)
    else:
        if "session_logs" not in st.session_state:
            st.session_state.session_logs = []

        st.session_state.session_logs.insert(
            0,
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "severity": severity,
                "module": module,
                "user_name": user_name,
                "action": action,
                "details": details,
            },
        )

        med_thresh = st.slider(
            "Medium risk cutoff", 0.10, float(high_thresh) - 0.05,
            float(cfg["tier_thresholds"]["medium"]), 0.01,
            help="Shipments above this score are flagged Medium Risk",
        )
        if sug_med:
            diff_m = round(med_thresh - sug_med, 2)
            arrow  = "↑ above" if diff_m > 0 else "↓ below" if diff_m < 0 else "matches"
            color  = "#22C55E" if abs(diff_m) <= 0.05 else "#F59E0B"
            st.markdown(
                f"<p style='font-size:11px;color:{color};margin:-8px 0 8px;'>"
                f"📊 Data suggests <strong>{sug_med}</strong> &nbsp;·&nbsp; "
                f"current is {abs(diff_m):.2f} {arrow} recommendation</p>",
                unsafe_allow_html=True,
            )

<<<<<<< HEAD
# =========================================================
# LOADERS
# =========================================================
def load_users() -> pd.DataFrame:
    query = f"""
        SELECT user_id, full_name, email, role, status, department,
               created_at, last_login, failed_attempts
        FROM {USERS_TABLE}
        ORDER BY user_id
    """
    df = run_select_query(query)
    return df if not df.empty else get_mock_users()


def load_shipments() -> pd.DataFrame:
    query = f"""
        SELECT shipment_id, lane, carrier, facility_type, appointment_type,
               base_freight_usd, accessorial_charge_usd, risk_score, risk_level,
               validation_status, uploaded_by, uploaded_at
        FROM {SHIPMENTS_TABLE}
        ORDER BY uploaded_at DESC
    """
    df = run_select_query(query)
    return df if not df.empty else get_mock_shipments()


def load_models() -> pd.DataFrame:
    query = f"""
        SELECT model_name, version, status, accuracy, auc_roc,
               last_trained, features
        FROM {MODEL_TABLE}
        ORDER BY model_name
    """
    df = run_select_query(query)
    return df if not df.empty else get_mock_models()


def load_logs() -> pd.DataFrame:
    query = f"""
        SELECT timestamp, severity, module, user_name, action, details
        FROM {LOGS_TABLE}
        ORDER BY timestamp DESC
    """
    df = run_select_query(query)
    if not df.empty:
        return df

    session_logs = st.session_state.get("session_logs", [])
    if session_logs:
        return pd.DataFrame(session_logs)

    return get_mock_logs()


# =========================================================
# UTIL
# =========================================================
def safe_text(val, default=""):
    if pd.isna(val):
        return default
    return str(val)


def render_info_card(title: str, body: str):
    st.markdown(
        dedent(f"""
<div class="admin-card">
    <div class="section-title">{title}</div>
    <div class="small-muted">{body}</div>
</div>
"""),
        unsafe_allow_html=True,
    )


def render_system_health_card(settings_dict: dict):
    st.markdown(
        dedent(f"""
<div class="admin-card">
    <div class="section-title">Core Services</div>
    <div class="small-muted" style="line-height:1.9;">
        Database Status: <b>{settings_dict['db_status']}</b><br>
        Prediction Pipeline: <b>{'Enabled' if settings_dict['prediction_pipeline'] else 'Disabled'}</b><br>
        Nightly Retraining: <b>{'Enabled' if settings_dict['nightly_retraining'] else 'Disabled'}</b><br>
        Maintenance Mode: <b>{'On' if settings_dict['maintenance_mode'] else 'Off'}</b>
    </div>
</div>
"""),
        unsafe_allow_html=True,
    )


# =========================================================
# STYLE
# =========================================================
st.markdown(
    dedent("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
.admin-card {
    background: #182033;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    color: white;
}
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: white;
}
.small-muted {
    color: #d4d7de;
    font-size: 0.95rem;
}
</style>
"""),
    unsafe_allow_html=True,
)

# =========================================================
# LOAD DATA
# =========================================================
load_settings()
settings = st.session_state.admin_settings

with st.spinner("Loading admin data..."):
    users_df = load_users()
    shipments_df = load_shipments()
    models_df = load_models()
    logs_df = load_logs()

db_live = has_db_connection()
settings["db_status"] = "Connected" if db_live else "Offline / Mock Mode"

# =========================================================
# HEADER
# =========================================================
st.title("🛠️ PACE Admin Control Center")
st.caption(
    "Administrative access for user governance, shipment data control, machine learning oversight, and system monitoring."
)
show_user_info()

if db_live:
    st.success("Live database connection detected.")
else:
    st.info("Database is unavailable right now, so the portal is running in mock mode.")

top_left, top_right = st.columns([4, 1])

with top_left:
    render_info_card("Admin Portal", f'Data source: <b>{settings["db_status"]}</b>')

with top_right:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# =========================================================
# KPI
# =========================================================
active_users = int((users_df["status"] == "Active").sum()) if "status" in users_df.columns else 0
locked_users = int((users_df["status"] == "Locked").sum()) if "status" in users_df.columns else 0
pending_reviews = int((shipments_df["validation_status"] == "Pending Review").sum()) if "validation_status" in shipments_df.columns else 0
high_risk_shipments = int((shipments_df["risk_level"] == "High").sum()) if "risk_level" in shipments_df.columns else 0
avg_risk = round(float(shipments_df["risk_score"].mean()), 1) if "risk_score" in shipments_df.columns else 0

active_model_name = "N/A"
if "status" in models_df.columns:
    active_model_df = models_df[models_df["status"] == "Active"]
    if not active_model_df.empty:
        active_model_name = str(active_model_df.iloc[0]["model_name"])

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Active Users", active_users)
m2.metric("Locked Users", locked_users)
m3.metric("Pending Reviews", pending_reviews)
m4.metric("High-Risk Shipments", high_risk_shipments)
m5.metric("Active Model", active_model_name)
m6.metric("Average Risk", f"{avg_risk}%")
=======
        col_save, col_reset = st.columns(2)
        with col_save:
            if st.button("Save Thresholds", type="primary", use_container_width=True):
                mcfg.set_thresholds(high_thresh, med_thresh)
                st.success("Thresholds saved.")
        with col_reset:
            if sug_high and sug_med:
                if st.button("Use Recommended", use_container_width=True):
                    mcfg.set_thresholds(sug_high, sug_med)
                    st.success(f"Set to recommended: High {sug_high} · Medium {sug_med}")
                    st.rerun()
>>>>>>> f816b21e6a81e7f212cc77be2e2f8c04286bfdbf

        st.markdown("<br>", unsafe_allow_html=True)

<<<<<<< HEAD
# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "📊 Overview",
        "👥 User Management",
        "📦 Data Governance",
        "🤖 Model Control",
        "⚙️ Risk & System Settings",
        "🧾 Audit Logs",
        "🛠️ Admin Tools",
    ]
)

# =========================================================
# TAB 1
# =========================================================
with tab1:
    c1, c2 = st.columns([1.2, 1])

    with c1:
        st.subheader("System Health")
        render_system_health_card(settings)

        st.write("")
        st.subheader("Recent Notifications")
        if not logs_df.empty:
            for _, row in logs_df.head(5).iterrows():
                st.info(f"[{row['severity']}] {row['module']} - {row['action']}: {row['details']}")
        else:
            st.info("No recent logs found.")

    with c2:
        st.subheader("Risk Distribution")
        if not shipments_df.empty and "risk_level" in shipments_df.columns:
            risk_counts = shipments_df["risk_level"].value_counts().reindex(["Low", "Medium", "High"]).fillna(0)
            st.bar_chart(risk_counts)
        else:
            st.warning("No shipment data found.")

        st.subheader("Validation Status")
        if not shipments_df.empty and "validation_status" in shipments_df.columns:
            st.bar_chart(shipments_df["validation_status"].value_counts())
        else:
            st.warning("No validation data found.")

# =========================================================
# TAB 5 SETTINGS FIX
# =========================================================
with tab5:
    st.subheader("Risk Thresholds and System Settings")

    sleft, sright = st.columns(2)

    with sleft:
        high_risk_threshold = st.slider("High Risk Threshold", 50, 95, settings["high_risk_threshold"])
        medium_risk_threshold = st.slider("Medium Risk Threshold", 10, 80, settings["medium_risk_threshold"])
        cost_alert_threshold = st.number_input(
            "Cost Alert Threshold (USD)",
            min_value=0,
            value=int(settings["cost_alert_threshold"]),
            step=25,
        )
        auto_lock_failed_attempts = st.slider(
            "Auto-lock after failed attempts",
            1,
            10,
            settings["auto_lock_failed_attempts"],
        )

        if st.button("Save Threshold Settings", use_container_width=True):
            settings["high_risk_threshold"] = high_risk_threshold
            settings["medium_risk_threshold"] = medium_risk_threshold
            settings["cost_alert_threshold"] = cost_alert_threshold
            settings["auto_lock_failed_attempts"] = auto_lock_failed_attempts
            add_log("INFO", "SETTINGS", username, "Save thresholds", "Updated threshold and security settings")
            st.success("Settings saved in session.")

    with sright:
        allow_csv_upload = st.toggle("Allow CSV Upload", value=settings["allow_csv_upload"])
        allow_manual_entry = st.toggle("Allow Manual Entry", value=settings["allow_manual_entry"])
        maintenance_mode = st.toggle("Maintenance Mode", value=settings["maintenance_mode"])
        nightly_retraining = st.toggle("Nightly Retraining", value=settings["nightly_retraining"])

        if st.button("Save System Controls", use_container_width=True):
            settings["allow_csv_upload"] = allow_csv_upload
            settings["allow_manual_entry"] = allow_manual_entry
            settings["maintenance_mode"] = maintenance_mode
            settings["nightly_retraining"] = nightly_retraining
            add_log("INFO", "SETTINGS", username, "Save controls", "Updated system control settings")
            st.success("System controls saved in session.")

    st.write("#### Current Settings")
    settings_df = pd.DataFrame(
        [{"setting": k, "value": str(v)} for k, v in settings.items()]
    )
    st.dataframe(settings_df, use_container_width=True)

# =========================================================
# SIMPLE PLACEHOLDERS FOR OTHER TABS
# =========================================================
with tab2:
    st.subheader("User Management")
    st.dataframe(users_df, use_container_width=True)

with tab3:
    st.subheader("Data Governance")
    st.dataframe(shipments_df, use_container_width=True)

with tab4:
    st.subheader("Model Control")
    st.dataframe(models_df, use_container_width=True)

with tab6:
    st.subheader("Audit Logs")
    st.dataframe(logs_df, use_container_width=True)

with tab7:
    st.subheader("Admin Tools")
    export_type = st.selectbox("Select Dataset", ["Users", "Shipments", "Models", "Logs", "Settings"])
    if st.button("Prepare Export Preview", use_container_width=True):
        if export_type == "Users":
            st.dataframe(users_df, use_container_width=True)
        elif export_type == "Shipments":
            st.dataframe(shipments_df, use_container_width=True)
        elif export_type == "Models":
            st.dataframe(models_df, use_container_width=True)
        elif export_type == "Logs":
            st.dataframe(logs_df, use_container_width=True)
        else:
            settings_df = pd.DataFrame(
                [{"setting": k, "value": str(v)} for k, v in settings.items()]
            )
            st.dataframe(settings_df, use_container_width=True)

st.divider()
st.success("PACE Admin Portal loaded successfully.")
=======
        # Auto-update settings
        st.markdown("**Auto-Update Settings**")
        auto_enabled = st.toggle(
            "Auto-update model when new records arrive",
            value=cfg.get("auto_update_enabled", True),
        )
        auto_threshold = st.number_input(
            "Update every N new records",
            min_value=10, max_value=10000,
            value=int(cfg.get("auto_update_threshold", 100)),
            step=10,
            disabled=not auto_enabled,
        )
        if st.button("Save Auto-Update Settings"):
            mcfg.set_auto_update(auto_enabled, auto_threshold)
            st.success("Auto-update settings saved.")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Train from CSV")
        st.caption(
            "Upload any shipment CSV to train the model on real data. "
            "Column names are auto-normalized — `detention_fee`, `demurrage`, `surcharge`, etc. "
            "are all recognized as accessorial charges."
        )

        train_file = st.file_uploader(
            "Drop training CSV here",
            type=["csv", "xlsx", "xls"],
            key="admin_train_upload",
        )

        if train_file is not None:
            try:
                if train_file.name.endswith((".xlsx", ".xls")):
                    import pandas as pd
                    train_df = pd.read_excel(train_file)
                else:
                    import pandas as pd
                    train_df = pd.read_csv(train_file)

                from utils.doc_parser import ensure_expected_columns
                train_df = ensure_expected_columns(train_df)

                st.info(f"{len(train_df):,} rows loaded · columns: {', '.join(train_df.columns.tolist())}")

                t0, t1_btn = st.columns(2)
                with t0:
                    if st.button("Incremental Update from File", type="primary", use_container_width=True):
                        with st.spinner("Updating model..."):
                            try:
                                metrics = incremental_update(train_df)
                                st.success(f"Updated! AUC: {metrics['auc']} · F1: {metrics['f1']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Update failed: {e}")
                with t1_btn:
                    if st.button("Full Retrain from File", use_container_width=True):
                        with st.spinner("Retraining from scratch..."):
                            try:
                                metrics = retrain(train_df)
                                st.success(f"Retrained! AUC: {metrics['auc']} · F1: {metrics['f1']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Retrain failed: {e}")
            except Exception as e:
                st.error(f"Could not read file: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Manual Training (Mock Data)")
        st.caption("Train on generated mock data — useful for testing the pipeline without a real dataset.")

        t1, t2 = st.columns(2)
        with t1:
            if st.button("Incremental Update", type="primary", use_container_width=True):
                with st.spinner("Updating model..."):
                    try:
                        df = generate_mock_shipments(500)
                        metrics = incremental_update(df)
                        st.success(f"Updated! AUC: {metrics['auc']} · F1: {metrics['f1']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update failed: {e}")

        with t2:
            if st.button("Full Retrain", use_container_width=True):
                with st.spinner("Retraining from scratch..."):
                    try:
                        df = generate_mock_shipments(1000)
                        metrics = retrain(df)
                        st.success(f"Retrained! AUC: {metrics['auc']} · F1: {metrics['f1']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Retrain failed: {e}")

with col_versions:
    with st.container(border=True):
        st.markdown("#### Version History")
        st.caption("Last 3 model versions. Roll back if a new update hurts performance.")

        versions = list_saved_versions()
        if not versions:
            st.info("No saved versions yet. Run a training event to create one.")
        else:
            for v in versions:
                m = v.get("metrics", {})
                auc_v = m.get("auc")
                f1_v  = m.get("f1")
                acc_v = m.get("accuracy")
                update_type = m.get("update_type", "full retrain")
                is_current  = (v["version"] == cfg.get("version", 0))

                label = f"v{v['version']}{'  ← current' if is_current else ''}"
                with st.expander(label, expanded=is_current):
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("AUC",      f"{auc_v:.3f}" if auc_v else "—")
                    mc2.metric("F1",       f"{f1_v:.3f}"  if f1_v  else "—")
                    mc3.metric("Accuracy", f"{acc_v:.3f}" if acc_v else "—")
                    st.caption(f"Type: {update_type} · Records: {m.get('n_train', 0) + m.get('n_test', 0)}")

                    if not is_current:
                        if st.button(f"Roll back to v{v['version']}", key=f"rollback_{v['version']}"):
                            ok = rollback_to_version(v["version"])
                            if ok:
                                st.success(f"Rolled back to v{v['version']}")
                                st.rerun()
                            else:
                                st.error("Rollback failed — model file not found.")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Last Trained")
        last = cfg.get("last_trained")
        if last:
            st.markdown(f"<p style='font-size:20px;font-weight:600'>{last}</p>", unsafe_allow_html=True)
        else:
            st.info("Model has not been trained yet.")

        f1_val  = cfg["metrics"].get("f1")
        acc_val = cfg["metrics"].get("accuracy")
        if f1_val or acc_val:
            mc1, mc2 = st.columns(2)
            mc1.metric("F1 Score", f"{f1_val:.3f}"  if f1_val  else "—")
            mc2.metric("Accuracy", f"{acc_val:.3f}" if acc_val else "—")
>>>>>>> f816b21e6a81e7f212cc77be2e2f8c04286bfdbf
