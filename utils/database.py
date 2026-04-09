import os
import hashlib
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

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
    try:
        return st.secrets["azure_sql"][key]
    except Exception:
        return os.getenv(key, "")


def get_db_config_status() -> Tuple[bool, str]:
    if not PYMSSQL_AVAILABLE:
        return False, "pymssql not installed"

    required = ["DB_SERVER", "DB_DATABASE", "DB_USERNAME", "DB_PASSWORD"]
    missing = [k for k in required if not _get_secret(k)]

    if missing:
        return False, f"Missing: {', '.join(missing)}"

    return True, "ok"


@st.cache_resource
def get_connection():
    ok, _ = get_db_config_status()
    if not ok:
        return None

    try:
        return pymssql.connect(
            server=_get_secret("DB_SERVER"),
            user=_get_secret("DB_USERNAME"),
            password=_get_secret("DB_PASSWORD"),
            database=_get_secret("DB_DATABASE"),
            port=1433,
            login_timeout=10,
            timeout=15,
            tds_version="7.4",
        )
    except Exception:
        return None


def test_connection() -> Tuple[bool, str]:
    ok, reason = get_db_config_status()
    if not ok:
        return False, reason

    try:
        conn = pymssql.connect(
            server=_get_secret("DB_SERVER"),
            user=_get_secret("DB_USERNAME"),
            password=_get_secret("DB_PASSWORD"),
            database=_get_secret("DB_DATABASE"),
            port=1433,
            login_timeout=10,
            timeout=15,
            tds_version="7.4",
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
        return True, "Connected successfully."
    except Exception as e:
        return False, f"Database connection failed: {e}"


def clear_db_cache():
    try:
        st.cache_data.clear()
    except Exception:
        pass

    try:
        st.cache_resource.clear()
    except Exception:
        pass


@st.cache_data
def get_tables(_conn) -> list[str]:
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
    if _conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql(f"SELECT TOP {row_limit} * FROM [{table_name}]", _conn)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_shipments(_conn) -> pd.DataFrame:
    if _conn is None:
        return pd.DataFrame()

    query = """
        SELECT
            s.ShipmentId AS shipment_id,
            s.ShipDate AS ship_date,
            c.carrier_name AS carrier,
            s.FacilityType AS facility,
            s.weight_lbs,
            s.DistanceMiles AS miles,
            s.LinehaulCost AS base_freight_usd,
            s.AccessorialCost AS accessorial_charge_usd,
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

        df["base_freight_usd"] = pd.to_numeric(df["base_freight_usd"], errors="coerce").fillna(0)
        df["accessorial_charge_usd"] = pd.to_numeric(df["accessorial_charge_usd"], errors="coerce").fillna(0)
        df["miles"] = pd.to_numeric(df["miles"], errors="coerce").fillna(0)

        df["total_cost_usd"] = (
            df["base_freight_usd"] + df["accessorial_charge_usd"]
        )

        df["cost_per_mile"] = (
            df["base_freight_usd"] / df["miles"].replace(0, float("nan"))
        ).fillna(0)

        df["lane"] = (
            df["OriginRegion"].fillna("?") + " → " + df["DestRegion"].fillna("?")
        )
        df["origin_city"] = df["OriginRegion"]
        df["destination_city"] = df["DestRegion"]

        return df

    except Exception:
        return pd.DataFrame()


@st.cache_data
def get_accessorial_charges(_conn, row_limit: int = 2000) -> pd.DataFrame:
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
def get_shipments_with_charges(_conn, row_limit: int = 2000) -> pd.DataFrame:
    if _conn is None:
        return pd.DataFrame()

    query = f"""
        SELECT TOP {row_limit}
            ac.charge_id,
            ac.shipment_id,
            ac.charge_type AS accessorial_type,
            ac.amount AS accessorial_charge_usd,
            ac.risk_flag,
            ac.invoice_date AS ship_date,
            ac.disputed,
            s.FacilityType AS facility,
            s.LinehaulCost AS base_freight_usd,
            s.risk_score,
            s.risk_tier,
            c.carrier_name AS carrier
        FROM Accessorial_Charges ac
        LEFT JOIN Shipments s ON ac.shipment_id = s.ShipmentId
        LEFT JOIN Carriers c ON s.CarrierId = c.carrier_id
        ORDER BY ac.invoice_date DESC
    """
    try:
        df = pd.read_sql(query, _conn)
        df["base_freight_usd"] = pd.to_numeric(df["base_freight_usd"], errors="coerce").fillna(0)
        df["accessorial_charge_usd"] = pd.to_numeric(df["accessorial_charge_usd"], errors="coerce").fillna(0)
        df["total_cost_usd"] = df["base_freight_usd"] + df["accessorial_charge_usd"]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data
def get_carriers(_conn) -> pd.DataFrame:
    if _conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql("SELECT * FROM Carriers ORDER BY carrier_name", _conn)
    except Exception:
        return pd.DataFrame()


@st.cache_data
def get_facilities(_conn) -> pd.DataFrame:
    if _conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql("SELECT * FROM Facilities ORDER BY facility_name", _conn)
    except Exception:
        return pd.DataFrame()


def verify_pace_user(_conn, username: str, password: str) -> Optional[str]:
    if _conn is None:
        return None

    username = username.lower().strip()
    pw_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        row = pd.read_sql(
            "SELECT role FROM PaceUsers WHERE LOWER(username) = %s AND password_hash = %s",
            _conn,
            params=(username, pw_hash),
        )
        if not row.empty:
            return row.iloc[0]["role"]
    except Exception:
        pass

    return None


def get_pace_users(_conn):
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


def create_pace_user(_conn, username, password, role):
    if _conn is None:
        return False, "No DB"

    username = str(username).strip().lower()
    role = str(role).strip().lower()

    if not username or not password:
        return False, "Username and password are required."

    if role not in {"user", "admin"}:
        return False, "Invalid role."

    pw_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        existing = pd.read_sql(
            "SELECT username FROM PaceUsers WHERE LOWER(username) = %s",
            _conn,
            params=(username,),
        )
        if not existing.empty:
            return False, f"User '{username}' already exists."

        cursor = _conn.cursor()
        cursor.execute(
            "INSERT INTO PaceUsers (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, pw_hash, role),
        )
        _conn.commit()
        clear_db_cache()
        return True, "Created"
    except Exception as e:
        return False, str(e)


def delete_pace_user(_conn, username, current_username: Optional[str] = None):
    if _conn is None:
        return False, "No DB"

    username = str(username).strip().lower()
    current_username = (current_username or "").strip().lower()

    if username == current_username:
        return False, "You cannot delete the currently logged-in admin."

    try:
        cursor = _conn.cursor()
        cursor.execute("DELETE FROM PaceUsers WHERE LOWER(username) = %s", (username,))
        _conn.commit()
        clear_db_cache()
        return True, "Deleted"
    except Exception as e:
        return False, str(e)


# =========================
# FALLBACK HELPERS
# =========================
def load_shipments_with_fallback(row_limit=1000):
    conn = get_connection()

    if conn:
        df = get_shipments(conn)
        if not df.empty:
            return df.head(row_limit)

    try:
        from utils.mock_data import generate_mock_shipments
        return generate_mock_shipments(min(row_limit, 300))
    except Exception:
        return pd.DataFrame()


def load_accessorial_with_fallback(row_limit=2000):
    conn = get_connection()

    if conn:
        df = get_shipments_with_charges(conn, row_limit=row_limit)
        if not df.empty:
            return df

    try:
        from utils.mock_data import generate_mock_shipments
        df = generate_mock_shipments(min(row_limit, 300)).copy()

        if "accessorial_type" not in df.columns:
            if "accessorial_charge_usd" in df.columns:
                df["accessorial_type"] = df["accessorial_charge_usd"].apply(
                    lambda x: "Accessorial" if float(x or 0) > 0 else "None"
                )
            else:
                df["accessorial_type"] = "None"

        if "total_cost_usd" not in df.columns:
            base = df["base_freight_usd"] if "base_freight_usd" in df.columns else 0
            acc = df["accessorial_charge_usd"] if "accessorial_charge_usd" in df.columns else 0
            df["total_cost_usd"] = base + acc

        return df
    except Exception:
        return pd.DataFrame()