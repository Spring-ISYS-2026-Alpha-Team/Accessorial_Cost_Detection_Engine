"""
utils/database.py
Azure SQL database connection for PACE.
Reads credentials from .env (local) or st.secrets (Streamlit Cloud).
"""
import os
import streamlit as st
import pandas as pd

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


@st.cache_data
def get_shipments(_conn, row_limit: int = 1000) -> pd.DataFrame:
    """
    Fetch shipment records from the database.
    Adjust the query to match your actual table/column names.
    """
    if _conn is None:
        return pd.DataFrame()
    query = f"""
        SELECT TOP {row_limit}
            shipment_id,
            ship_date,
            carrier,
            facility,
            weight_lbs,
            miles,
            base_freight_usd,
            accessorial_charge_usd
        FROM shipments
        ORDER BY ship_date DESC
    """
    try:
        return pd.read_sql(query, _conn)
    except Exception:
        return pd.DataFrame()
