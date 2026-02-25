import os
import pyodbc
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load credentials from .env file in the project root
load_dotenv()


# --- Database Connection ---

@st.cache_resource
def get_connection():
    """Create a cached SQL Server connection using credentials from .env."""
    conn_str = (
        f"DRIVER={{{os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')}}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
    )
    return pyodbc.connect(conn_str)


@st.cache_data
def get_tables(_conn):
    """Fetch all base table names from the database, sorted alphabetically."""
    query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """
    return pd.read_sql(query, _conn)["TABLE_NAME"].tolist()


@st.cache_data
def get_table_data(_conn, table_name: str, row_limit: int) -> pd.DataFrame:
    """
    Fetch up to row_limit rows from the selected table.
    TOP is used instead of LIMIT — required syntax for MS SQL Server.
    Capped to avoid memory issues with large tables (1,000+ rows).
    """
    query = f"SELECT TOP {row_limit} * FROM [{table_name}]"
    return pd.read_sql(query, _conn)


# --- Page Config ---

st.set_page_config(
    page_title="PACE Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)

st.title("PACE — Predictive Accessorial Cost Detection Engine")
st.caption("MS SQL Server Table Viewer")

# --- Connect to Database ---

try:
    conn = get_connection()
except Exception as e:
    st.error(f"Could not connect to SQL Server. Check your .env credentials.\n\n{e}")
    st.stop()

# --- Sidebar Controls ---

with st.sidebar:
    st.header("Controls")

    tables = get_tables(conn)

    if not tables:
        st.warning("No tables found in the database.")
        st.stop()

    selected_table = st.selectbox("Select Table", tables)

    # Row limit slider — keeps large tables from slowing down the UI
    row_limit = st.slider(
        "Row Limit",
        min_value=100,
        max_value=5000,
        value=500,
        step=100,
        help="Limits rows loaded for performance. Increase carefully on large tables.",
    )

# --- Main: Table Display ---

st.subheader(f"Table: `{selected_table}`")

df = get_table_data(conn, selected_table, row_limit)

st.caption(f"Showing {len(df):,} rows × {len(df.columns):,} columns")

# use_container_width fills the page; hide_index keeps it clean
st.dataframe(df, use_container_width=True, hide_index=True)
