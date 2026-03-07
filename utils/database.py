"""
utils/database.py
Azure SQL database connection for PACE.
Reads credentials from st.secrets (Streamlit Cloud) or os.environ (local).
"""
import os
import streamlit as st
import pandas as pd

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

# ── Connection constants ───────────────────────────────────────────────────────
_DB_SERVER = "essql1.database.windows.net"
_DB_NAME   = "ISYS43603_Spring2026_Sec02_Alice_db"
_DB_DRIVER = "ODBC Driver 18 for SQL Server"

# ── Expected columns returned by load_shipments() on success or failure ───────
_SHIPMENT_COLUMNS = [
    "shipment_id", "ship_date", "carrier", "facility",
    "origin_city", "destination_city", "lane",
    "weight_lbs", "miles", "base_freight_usd", "accessorial_charge_usd",
    "total_cost_usd", "cost_per_mile", "risk_score", "risk_tier",
    "accessorial_type",
    "Revenue", "safety_rating", "fleet_size",
    "facility_city", "facility_state", "fac_type",
    "avg_dwell_time_hrs", "appointment_required",
]

# ── SQL queries ────────────────────────────────────────────────────────────────
_SHIPMENTS_QUERY = """
SELECT
    s.ShipmentId,
    s.ShipDate,
    s.OriginRegion,
    s.DestRegion,
    s.CarrierId,
    s.FacilityType,
    s.AppointmentType,
    s.DistanceMiles,
    s.weight_lbs,
    s.Revenue,
    s.LinehaulCost,
    s.AccessorialFlag,
    s.AccessorialCost,
    s.risk_score,
    s.risk_tier,
    c.carrier_name,
    c.safety_rating,
    c.fleet_size,
    f.facility_name,
    f.city  AS facility_city,
    f.state AS facility_state,
    f.facility_type AS fac_type,
    f.avg_dwell_time_hrs,
    f.appointment_required
FROM Shipments s
JOIN Carriers c ON s.CarrierId = c.carrier_id
LEFT JOIN Facilities f ON s.facility_id = f.facility_id
"""

_ACCESSORIAL_QUERY = """
SELECT
    ac.charge_id,
    ac.shipment_id,
    ac.charge_type,
    ac.amount,
    ac.risk_flag,
    ac.invoice_date,
    ac.disputed,
    ac.notes,
    s.CarrierId,
    c.carrier_name,
    s.facility_id,
    f.facility_name
FROM Accessorial_Charges ac
JOIN Shipments s ON ac.shipment_id = s.ShipmentId
JOIN Carriers c ON s.CarrierId = c.carrier_id
LEFT JOIN Facilities f ON s.facility_id = f.facility_id
"""


# ── Connection helper ──────────────────────────────────────────────────────────

def get_connection():
    """
    Open and return a pyodbc connection to Azure SQL.

    Credential resolution order:
    1. st.secrets["azure_sql"] with keys server/database/username/password
       (Streamlit Cloud / local secrets.toml)
    2. Environment variables AZURE_SQL_SERVER / AZURE_SQL_DATABASE /
       AZURE_SQL_USERNAME / AZURE_SQL_PASSWORD (local dev)
    3. Returns None if credentials are missing or placeholder values

    Returns pyodbc.Connection, or None if credentials are not configured.
    Raises on connection error so callers can catch and surface warnings.
    """
    if not PYODBC_AVAILABLE:
        return None

    try:
        sec      = st.secrets["azure_sql"]
        server   = sec.get("server",   _DB_SERVER)
        database = sec.get("database", _DB_NAME)
        username = sec.get("username", "")
        password = sec.get("password", "")
    except (KeyError, FileNotFoundError, AttributeError):
        server   = os.getenv("AZURE_SQL_SERVER",   _DB_SERVER)
        database = os.getenv("AZURE_SQL_DATABASE", _DB_NAME)
        username = os.getenv("AZURE_SQL_USERNAME", "YOUR_USERNAME_HERE")
        password = os.getenv("AZURE_SQL_PASSWORD", "YOUR_PASSWORD_HERE")

    # Return None (not an error) when credentials are not yet filled in
    if not username or username == "YOUR_USERNAME_HERE":
        return None
    if not password or password == "YOUR_PASSWORD_HERE":
        return None

    conn_str = (
        f"DRIVER={{{_DB_DRIVER}}};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)


# ── Data loaders ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_shipments() -> pd.DataFrame:
    """
    Load shipment data from Azure SQL and return a DataFrame whose column
    names match exactly what all Streamlit pages expect.

    Column mapping applied after the SQL query:
    - ShipmentId      → shipment_id  ("SHP-00001" format)
    - ShipDate        → ship_date    ("YYYY-MM-DD" string)
    - carrier_name    → carrier
    - facility_name   → facility     (falls back to "Unknown" on LEFT JOIN null)
    - OriginRegion    → origin_city  (state abbreviation used as label)
    - DestRegion      → destination_city
    - derived         → lane         (OriginRegion + " → " + DestRegion)
    - DistanceMiles   → miles        (int)
    - LinehaulCost    → base_freight_usd
    - AccessorialCost → accessorial_charge_usd
    - derived         → total_cost_usd  (base + accessorial)
    - derived         → cost_per_mile   (total / miles; 0 when miles == 0)
    - risk_score      stays as risk_score (float)
    - risk_tier       stays as risk_tier  (str)
    - derived         → accessorial_type ("Detention" if AccessorialFlag==1 else "None")

    Extra SQL columns are preserved in the returned DataFrame:
    Revenue, safety_rating, fleet_size, facility_city, facility_state,
    fac_type, avg_dwell_time_hrs, appointment_required.

    Returns an empty DataFrame with the correct columns if the database
    connection fails, so pages degrade gracefully instead of crashing.
    Decorated with @st.cache_data(ttl=300) — do NOT wrap calls in a
    second @st.cache_data layer on the calling page.
    """
    try:
        conn = get_connection()
    except Exception as exc:
        st.warning(f"Database connection failed: {exc}")
        return pd.DataFrame(columns=_SHIPMENT_COLUMNS)

    if conn is None:
        st.warning(
            "Database credentials are not configured. "
            "Add your credentials to .streamlit/secrets.toml "
            "(see .streamlit/secrets.toml.example) or set the "
            "AZURE_SQL_USERNAME / AZURE_SQL_PASSWORD environment variables."
        )
        return pd.DataFrame(columns=_SHIPMENT_COLUMNS)

    try:
        df = pd.read_sql(_SHIPMENTS_QUERY, conn)
    except Exception as exc:
        st.warning(f"Failed to load shipments from database: {exc}")
        return pd.DataFrame(columns=_SHIPMENT_COLUMNS)
    finally:
        conn.close()

    # ── shipment_id ───────────────────────────────────────────────────────────
    df["shipment_id"] = df["ShipmentId"].apply(lambda x: f"SHP-{int(x):05d}")

    # ── ship_date ─────────────────────────────────────────────────────────────
    df["ship_date"] = pd.to_datetime(df["ShipDate"]).dt.strftime("%Y-%m-%d")

    # ── carrier / facility (LEFT JOIN may produce nulls for facility) ─────────
    df["carrier"]  = df["carrier_name"].fillna("Unknown")
    df["facility"] = df["facility_name"].fillna("Unknown")

    # ── origin / destination (state abbreviations used as city labels) ────────
    df["origin_city"]      = df["OriginRegion"].fillna("")
    df["destination_city"] = df["DestRegion"].fillna("")
    df["lane"] = df["OriginRegion"].fillna("") + " → " + df["DestRegion"].fillna("")

    # ── miles ─────────────────────────────────────────────────────────────────
    df["miles"] = df["DistanceMiles"].fillna(0).astype(int)

    # ── cost columns ──────────────────────────────────────────────────────────
    df["base_freight_usd"]       = df["LinehaulCost"].fillna(0).astype(float)
    df["accessorial_charge_usd"] = df["AccessorialCost"].fillna(0).astype(float)
    df["total_cost_usd"]         = df["base_freight_usd"] + df["accessorial_charge_usd"]

    # cost per mile — avoid division by zero
    safe_miles = df["miles"].replace(0, float("nan"))
    df["cost_per_mile"] = (df["total_cost_usd"] / safe_miles).fillna(0.0)

    # ── risk columns (already in DB) ──────────────────────────────────────────
    df["risk_score"] = df["risk_score"].fillna(0.0).astype(float)
    df["risk_tier"]  = df["risk_tier"].fillna("Low").astype(str)

    # ── accessorial_type (derived from AccessorialFlag bit column) ────────────
    df["accessorial_type"] = df["AccessorialFlag"].apply(
        lambda x: "Detention" if x == 1 else "None"
    )

    # ── ensure numeric types ──────────────────────────────────────────────────
    df["weight_lbs"]        = df["weight_lbs"].fillna(0).astype(int)
    df["Revenue"]           = df["Revenue"].fillna(0).astype(float)
    df["fleet_size"]        = df["fleet_size"].fillna(0)
    df["avg_dwell_time_hrs"] = df["avg_dwell_time_hrs"].fillna(0)

    return df


@st.cache_data(ttl=300)
def load_accessorial_charges() -> pd.DataFrame:
    """
    Load accessorial charge detail records joined to Shipments, Carriers,
    and Facilities.

    Returns an empty DataFrame on connection failure so pages degrade
    gracefully.
    """
    try:
        conn = get_connection()
    except Exception as exc:
        st.warning(f"Database connection failed: {exc}")
        return pd.DataFrame()

    if conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql(_ACCESSORIAL_QUERY, conn)
    except Exception as exc:
        st.warning(f"Failed to load accessorial charges: {exc}")
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data(ttl=300)
def load_carriers() -> pd.DataFrame:
    """
    Load all rows from the Carriers table.
    Returns an empty DataFrame on connection failure.
    """
    try:
        conn = get_connection()
    except Exception as exc:
        st.warning(f"Database connection failed: {exc}")
        return pd.DataFrame()

    if conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql("SELECT * FROM Carriers", conn)
    except Exception as exc:
        st.warning(f"Failed to load carriers: {exc}")
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data(ttl=300)
def load_facilities() -> pd.DataFrame:
    """
    Load all rows from the Facilities table.
    Returns an empty DataFrame on connection failure.
    """
    try:
        conn = get_connection()
    except Exception as exc:
        st.warning(f"Database connection failed: {exc}")
        return pd.DataFrame()

    if conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql("SELECT * FROM Facilities", conn)
    except Exception as exc:
        st.warning(f"Failed to load facilities: {exc}")
        return pd.DataFrame()
    finally:
        conn.close()
