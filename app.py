# File: app.py
import os
import pyodbc
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from auth_utils import logout, check_auth

# Load credentials from .env file in the project root
load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="PACE Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- Authentication Screen (Mock for PB-4 Testing) ---
# Note: In PB-2 (Login), this will be replaced with real DB credential validation.
if not st.session_state['authenticated']:
    st.title("🔒 PACE Secure Login")
    st.markdown("Please authenticate to access shipment data.")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username and password:
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.rerun()
            else:
                st.error("Please enter both username and password.")
    st.stop() # Stop execution here if not logged in

# --- Main Application (Protected) ---

# Sidebar Navigation & Logout
with st.sidebar:
    st.title("PACE Navigation")
    st.write(f"👤 User: **{st.session_state.get('username', 'Unknown')}**")
    st.divider()
    
    # 🛑 PB-4 IMPLEMENTATION: Secure Logout Button
    if st.button("🔒 Log Out Securely", use_container_width=True, type="secondary"):
        logout()
    
    st.divider()
    st.info("Session Active ✅")

# --- Database Connection (Protected Behind Auth) ---
@st.cache_resource
def get_connection():
    """Create a cached SQL Server connection using credentials from .env."""
    try:
        conn_str = (
            f"DRIVER={{{os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')}}};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_DATABASE')};"
            f"UID={os.getenv('DB_USERNAME')};"
            f"PWD={os.getenv('DB_PASSWORD')};"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error(f"Database Connection Failed: {e}")
        return None

@st.cache_data
def get_tables(_conn):
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
    except:
        return []

@st.cache_data
def get_table_data(_conn, table_name: str, row_limit: int) -> pd.DataFrame:
    """Fetch up to row_limit rows from the selected table."""
    if _conn is None:
        return pd.DataFrame()
    query = f"SELECT TOP {row_limit} * FROM [{table_name}]"
    try:
        return pd.read_sql(query, _conn)
    except:
        return pd.DataFrame()

# --- Main Dashboard Content ---
st.title("PACE — Predictive Accessorial Cost Detection Engine")
st.caption("MS SQL Server Table Viewer")

# Connect to Database
conn = get_connection()

if conn:
    # --- Sidebar Controls ---
    with st.sidebar:
        st.header("Data Controls")
        tables = get_tables(conn)

        if not tables:
            st.warning("No tables found in the database.")
        else:
            selected_table = st.selectbox("Select Table", tables)
            row_limit = st.slider(
                "Row Limit",
                min_value=100,
                max_value=5000,
                value=500,
                step=100,
            )

    # --- Main: Table Display ---
    if tables:
        st.subheader(f"Table: `{selected_table}`")
        df = get_table_data(conn, selected_table, row_limit)
        st.caption(f"Showing {len(df):,} rows × {len(df.columns):,} columns")
        st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.error("Unable to connect to database. Please check .env credentials.")