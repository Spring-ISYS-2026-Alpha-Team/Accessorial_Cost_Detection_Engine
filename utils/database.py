"""
utils/database.py
Azure SQL database connection for PACE.
Reads credentials from .env (local) or st.secrets (Streamlit Cloud).
"""
import os
import hashlib
import streamlit as st
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False


def _get_secret(key: str) -> str:
    """Read a secret from st.secrets (cloud) or os.environ (local)."""
    try:
        return st.secrets["azure_sql"][key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, "")


@st.cache_resource
def get_connection():
    """
    Return a cached pyodbc connection to Azure SQL.
    Returns None and shows an error if connection fails.
    """
    if not PYODBC_AVAILABLE:
        st.error("pyodbc is not installed. Run: pip install pyodbc")
        return None

    server   = _get_secret("DB_SERVER")
    database = _get_secret("DB_DATABASE")
    username = _get_secret("DB_USERNAME")
    password = _get_secret("DB_PASSWORD")
    driver   = _get_secret("DB_DRIVER") or "ODBC Driver 18 for SQL Server"

    if not all([server, database, username, password]):
        return None  # Credentials not configured — caller falls back to mock data

    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )

    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error(f"Azure SQL connection failed: {e}")
        return None


@st.cache_data(ttl=300)
def get_tables(_conn) -> list[str]:
    """Return list of user table names from the database."""
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


@st.cache_data(ttl=300)
def get_table_data(_conn, table_name: str, row_limit: int = 500) -> pd.DataFrame:
    """Fetch up to row_limit rows from a table."""
    if _conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql(f"SELECT TOP {row_limit} * FROM [{table_name}]", _conn)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_shipments(_conn, row_limit: int = 1000) -> pd.DataFrame:
    """Fetch shipment records joined with carrier name."""
    if _conn is None:
        return pd.DataFrame()
    query = f"""
        SELECT TOP {row_limit}
            s.ShipmentId       AS shipment_id,
            s.ShipDate         AS ship_date,
            c.carrier_name     AS carrier,
            c.dot_number,
            s.FacilityType     AS facility,
            s.weight_lbs,
            s.DistanceMiles    AS miles,
            s.LinehaulCost     AS base_freight_usd,
            s.AccessorialCost  AS accessorial_charge_usd,
            s.OriginRegion,
            s.DestRegion,
            s.Revenue,
            s.AccessorialFlag,
            s.risk_score,
            s.risk_tier,
            s.AppointmentType
        FROM Shipments s
        LEFT JOIN Carriers c ON s.CarrierId = c.carrier_id
        ORDER BY s.ShipDate DESC
    """
    try:
        df = pd.read_sql(query, _conn)
        df["total_cost_usd"] = df["base_freight_usd"] + df["accessorial_charge_usd"]
        df["cost_per_mile"] = (
            df["base_freight_usd"] / df["miles"].replace(0, float("nan"))
        ).fillna(0)
        df["lane"] = df["OriginRegion"].fillna("?") + " → " + df["DestRegion"].fillna("?")
        df["origin_city"]      = df["OriginRegion"]
        df["destination_city"] = df["DestRegion"]
        return df
    except Exception:
        return pd.DataFrame()


def load_shipments_with_fallback(_conn, row_limit: int = 1000) -> pd.DataFrame:
    """
    Return shipment data from Azure SQL merged with any uploaded+scored CSV
    stored in st.session_state['upload_scored'].

    - If Azure SQL is available: starts from the DB records.
    - If upload_scored exists: appended as additional rows (missing cols filled with NaN).
    - If neither is available: returns empty DataFrame.
    """
    db_df     = get_shipments(_conn, row_limit) if _conn is not None else pd.DataFrame()
    upload_df = st.session_state.get("upload_scored")

    if upload_df is None or upload_df.empty:
        return db_df if not db_df.empty else pd.DataFrame()

    # Align uploaded data to match the DB column set
    upload_aligned = upload_df.copy()
    upload_aligned["data_source"] = "uploaded"
    if not db_df.empty:
        db_df["data_source"] = "database"
        combined = pd.concat([db_df, upload_aligned], ignore_index=True, sort=False)
    else:
        combined = upload_aligned

    # Ensure derived columns exist
    if "total_cost_usd" not in combined.columns:
        b = pd.to_numeric(combined.get("base_freight_usd"), errors="coerce").fillna(0)
        a = pd.to_numeric(combined.get("accessorial_charge_usd"), errors="coerce").fillna(0)
        combined["total_cost_usd"] = b + a
    if "cost_per_mile" not in combined.columns:
        miles = pd.to_numeric(combined.get("miles"), errors="coerce").replace(0, float("nan"))
        combined["cost_per_mile"] = (
            pd.to_numeric(combined.get("base_freight_usd"), errors="coerce").fillna(0) / miles
        ).fillna(0)
    if "lane" not in combined.columns:
        combined["lane"] = (
            combined.get("OriginRegion", combined.get("origin_city", pd.Series(["?"] * len(combined)))).fillna("?")
            + " → "
            + combined.get("DestRegion", combined.get("destination_city", pd.Series(["?"] * len(combined)))).fillna("?")
        )

    return combined


@st.cache_data(ttl=300)
def get_accessorial_charges(_conn, row_limit: int = 2000) -> pd.DataFrame:
    """Fetch accessorial charge records."""
    if _conn is None:
        return pd.DataFrame()
    query = f"""
        SELECT TOP {row_limit}
            ac.charge_id,
            ac.shipment_id,
            ac.charge_type,
            ac.amount,
            ac.risk_flag,
            ac.invoice_date,
            ac.disputed,
            ac.dispute_resolved,
            ac.notes
        FROM Accessorial_Charges ac
        ORDER BY ac.invoice_date DESC
    """
    try:
        return pd.read_sql(query, _conn)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_carriers(_conn) -> pd.DataFrame:
    """Fetch all carrier records."""
    if _conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM Carriers ORDER BY carrier_name", _conn)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_facilities(_conn) -> pd.DataFrame:
    """Fetch all facility records."""
    if _conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM Facilities ORDER BY facility_name", _conn)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_shipments_with_charges(_conn, row_limit: int = 2000) -> pd.DataFrame:
    """
    Accessorial Charges joined to Shipment + Carrier for the Accessorial Tracker page.
    Returns one row per charge with carrier/facility context.
    """
    if _conn is None:
        return pd.DataFrame()
    query = f"""
        SELECT TOP {row_limit}
            ac.charge_id,
            ac.shipment_id,
            ac.charge_type        AS accessorial_type,
            ac.amount             AS accessorial_charge_usd,
            ac.risk_flag,
            ac.invoice_date       AS ship_date,
            ac.disputed,
            s.FacilityType        AS facility,
            s.LinehaulCost        AS base_freight_usd,
            s.risk_score,
            s.risk_tier,
            c.carrier_name        AS carrier
        FROM Accessorial_Charges ac
        LEFT JOIN Shipments s  ON ac.shipment_id = s.ShipmentId
        LEFT JOIN Carriers  c  ON s.CarrierId    = c.carrier_id
        ORDER BY ac.invoice_date DESC
    """
    try:
        df = pd.read_sql(query, _conn)
        df["total_cost_usd"] = df["base_freight_usd"].fillna(0) + df["accessorial_charge_usd"].fillna(0)
        return df
    except Exception:
        return pd.DataFrame()


# ── User management (PaceUsers table) ─────────────────────────────────────────

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _ensure_users_table(conn) -> None:
    """Create PaceUsers table if it doesn't exist, seed default accounts."""
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'PaceUsers'
        )
        BEGIN
            CREATE TABLE PaceUsers (
                username     NVARCHAR(100) PRIMARY KEY,
                password_hash NVARCHAR(64) NOT NULL,
                role         NVARCHAR(20)  NOT NULL DEFAULT 'user',
                created_at   DATETIME      NOT NULL DEFAULT GETDATE()
            );
            INSERT INTO PaceUsers (username, password_hash, role) VALUES
                ('admin', ?, 'admin'),
                ('user',  ?, 'user');
        END
    """, _hash_password("admin"), _hash_password("user"))
    conn.commit()


def get_pace_users(conn) -> pd.DataFrame:
    """Return all PaceUsers rows (no password hashes)."""
    if conn is None:
        return pd.DataFrame()
    try:
        _ensure_users_table(conn)
        return pd.read_sql(
            "SELECT username AS Username, role AS Role, created_at AS [Created At] FROM PaceUsers ORDER BY created_at",
            conn,
        )
    except Exception:
        return pd.DataFrame()


def create_pace_user(conn, username: str, password: str, role: str) -> str:
    """
    Insert a new user. Returns '' on success or an error message string.
    """
    if conn is None:
        return "No database connection."
    try:
        _ensure_users_table(conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM PaceUsers WHERE username = ?", username
        )
        if cursor.fetchone():
            return f"Username '{username}' already exists."
        cursor.execute(
            "INSERT INTO PaceUsers (username, password_hash, role) VALUES (?, ?, ?)",
            username, _hash_password(password), role,
        )
        conn.commit()
        return ""
    except Exception as e:
        return str(e)


def delete_pace_user(conn, username: str) -> str:
    """Delete a user by username. Returns '' on success or error string."""
    if conn is None:
        return "No database connection."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM PaceUsers WHERE username = ?", username)
        conn.commit()
        return ""
    except Exception as e:
        return str(e)


def verify_pace_user(conn, username: str, password: str):
    """
    Verify credentials against PaceUsers table.
    Returns role string on success, None on failure.
    Falls back gracefully if table/connection unavailable.
    """
    if conn is None:
        return None
    try:
        _ensure_users_table(conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role FROM PaceUsers WHERE username = ? AND password_hash = ?",
            username, _hash_password(password),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception:
        return None
