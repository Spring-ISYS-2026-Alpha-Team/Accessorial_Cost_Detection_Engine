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
    import pymssql
    PYMSSQL_AVAILABLE = True
except ImportError:
    PYMSSQL_AVAILABLE = False


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
    if not PYMSSQL_AVAILABLE:
        return None

    server   = _get_secret("DB_SERVER")
    database = _get_secret("DB_DATABASE")
    username = _get_secret("DB_USERNAME")
    password = _get_secret("DB_PASSWORD")

    if not all([server, database, username, password]):
        return None  # Credentials not configured — caller falls back to mock data

    try:
        return pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database,
            port=1433,
            login_timeout=10,
            tds_version="7.4",
        )
    except Exception as e:
        st.warning(f"Database connection failed: {e}")
        return None


@st.cache_data
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


@st.cache_data
def get_table_data(_conn, table_name: str, row_limit: int = 500) -> pd.DataFrame:
    """Fetch up to row_limit rows from a table."""
    if _conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql(f"SELECT TOP {row_limit} * FROM [{table_name}]", _conn)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_shipments(_conn) -> pd.DataFrame:
    """Fetch all shipment records joined with carrier name."""
    if _conn is None:
        return pd.DataFrame()
    query = """
        SELECT
            s.ShipmentId       AS shipment_id,
            s.ShipDate         AS ship_date,
            c.carrier_name     AS carrier,
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


@st.cache_data
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


@st.cache_data
def get_carriers(_conn) -> pd.DataFrame:
    """Fetch all carrier records."""
    if _conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM Carriers ORDER BY carrier_name", _conn)
    except Exception:
        return pd.DataFrame()


@st.cache_data
def get_facilities(_conn) -> pd.DataFrame:
    """Fetch all facility records."""
    if _conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM Facilities ORDER BY facility_name", _conn)
    except Exception:
        return pd.DataFrame()


def verify_pace_user(_conn, username: str, password: str):
    """
    Verify a username/password against the PaceUsers table.
    Passwords are stored as SHA-256 hex digests.
    Returns the user's role string on success, None on failure.
    """
    if _conn is None:
        return None
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        row = pd.read_sql(
            "SELECT role FROM PaceUsers WHERE username = %s AND password_hash = %s",
            _conn,
            params=(username, pw_hash),
        )
        if not row.empty:
            return str(row.iloc[0]["role"])
    except Exception:
        pass
    return None


def get_pace_users(_conn) -> pd.DataFrame:
    """Return all PaceUsers rows (no password_hash)."""
    if _conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql(
            "SELECT username, role, created_at FROM PaceUsers ORDER BY username",
            _conn,
        )
    except Exception:
        try:
            return pd.read_sql("SELECT username, role FROM PaceUsers ORDER BY username", _conn)
        except Exception:
            return pd.DataFrame()


def create_pace_user(_conn, username: str, password: str, role: str) -> tuple[bool, str]:
    """Insert a new user into PaceUsers. Returns (success, message)."""
    if _conn is None:
        return False, "No database connection."
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor = _conn.cursor()
        cursor.execute(
            "INSERT INTO PaceUsers (username, password_hash, role) VALUES (%s, %s, %s)",
            (username.strip(), pw_hash, role),
        )
        _conn.commit()
        return True, f"User '{username}' created successfully."
    except Exception as e:
        return False, str(e)


def delete_pace_user(_conn, username: str) -> tuple[bool, str]:
    """Delete a user from PaceUsers by username."""
    if _conn is None:
        return False, "No database connection."
    try:
        cursor = _conn.cursor()
        cursor.execute("DELETE FROM PaceUsers WHERE username = %s", (username,))
        _conn.commit()
        return True, f"User '{username}' deleted."
    except Exception as e:
        return False, str(e)


@st.cache_data
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
