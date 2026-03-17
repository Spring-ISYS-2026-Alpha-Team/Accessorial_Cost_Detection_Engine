import streamlit as st
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

st.divider()

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