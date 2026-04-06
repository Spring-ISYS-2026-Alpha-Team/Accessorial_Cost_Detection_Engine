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
    Return a cached pymssql connection to Azure SQL.
    Retries up to 3 times with a 2-second delay before giving up.
    Returns None if all attempts fail.
    
    NOTE: Uses @st.cache_resource so the connection is shared across
    all sessions and reruns — avoids reconnecting on every page load.
    The connection is tested with SELECT 1 before being returned.
    """
    import time

    if not PYMSSQL_AVAILABLE:
        return None

    server   = _get_secret("DB_SERVER")
    database = _get_secret("DB_DATABASE")
    username = _get_secret("DB_USERNAME")
    password = _get_secret("DB_PASSWORD")

    missing = [k for k, v in {"DB_SERVER": server, "DB_DATABASE": database,
                                "DB_USERNAME": username, "DB_PASSWORD": password}.items() if not v]
    if missing:
        return None

    last_err = None
    for attempt in range(1, 4):
        try:
            conn = pymssql.connect(
                server=server,
                user=username,
                password=password,
                database=database,
                port=1433,
                login_timeout=20,
                tds_version="7.4",
            )
            # Smoke-test: ensure the connection is usable
            conn.cursor().execute("SELECT 1")
            return conn
        except Exception as e:
            last_err = e
            if attempt < 3:
                time.sleep(2)

    # All retries exhausted — fail silently, fallback to demo data
    return None


def get_connection_safe():
    """
    Wrapper around get_connection() that returns None if the cached
    connection has gone stale (e.g. Azure SQL idle timeout) rather than
    raising an error. Clears the cache and retries once if the connection
    fails the liveness check.
    """
    conn = get_connection()
    if conn is None:
        return None
    try:
        conn.cursor().execute("SELECT 1")
        return conn
    except Exception:
        # Connection went stale — clear cache and get a fresh one
        get_connection.clear()
        return get_connection()


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
        return pd.read_sql(f"SELECT TOP {row_limit} * FROM [{table_name}]", _conn)  # nosec B608
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
            s.AppointmentType,
        c.dot_number
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
        # M-3: Normalize risk_score to 0-100 if stored as 0-1 in the DB
        if "risk_score" in df.columns:
            max_score = df["risk_score"].max()
            if max_score <= 1.0:
                df["risk_score"] = (df["risk_score"] * 100).round(2)
        return df
    except Exception:
        return pd.DataFrame()


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
    """  # nosec B608
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


def load_shipments_from_teradata(row_limit: int = 10000) -> pd.DataFrame:
    """
    Pull records from the Teradata training view and reshape them into the
    dashboard schema (same column names as get_shipments()).

    Column mapping:
        dot_number              → shipment_id
        insp_year / insp_month  → ship_date  (YYYY-MM-01)
        dot_number (str)        → carrier
        carrier_phy_state       → facility, OriginRegion, DestRegion
        accessorial_risk_score  → risk_score  (0–100 scaled)
        accessorial_type        → risk_tier   (label)
        sms_nbr_power_unit      → weight_lbs  (proxy)
        carrier_mcs150_mileage  → miles       (proxy)
    Columns with no natural proxy are set to 0 / "Unknown".
    """
    try:
        import os
        td_host = os.getenv("TD_HOST", "")
        td_user = os.getenv("TD_USERNAME", "")
        td_pass = os.getenv("TD_PASSWORD", "")
        td_db   = os.getenv("TD_DATABASE", "CTGAN")
        td_view = os.getenv("TD_VIEW", "pace_synthetic_v")

        if not td_host:
            return pd.DataFrame()

        import teradatasql
        conn = teradatasql.connect(
            host=td_host, user=td_user,
            password=td_pass, database=td_db,
        )

        query = f"""
            SELECT TOP {row_limit}
                dot_number,
                insp_year,
                insp_month,
                carrier_phy_state,
                sms_nbr_power_unit,
                carrier_mcs150_mileage,
                accessorial_risk_score,
                accessorial_type
            FROM {td_db}.{td_view}
            WHERE accessorial_risk_score IS NOT NULL
            ORDER BY insp_year DESC, insp_month DESC
        """  # nosec B608
        raw = pd.read_sql(query, conn)
        conn.close()

        if raw.empty:
            return pd.DataFrame()

        # ── Map to dashboard schema ──────────────────────────────────────
        df = pd.DataFrame()
        df["shipment_id"]          = raw["dot_number"].astype(str)
        df["carrier"]              = "DOT-" + raw["dot_number"].astype(str)

        # Build a ship_date from inspection year + month
        year  = pd.to_numeric(raw["insp_year"],  errors="coerce").fillna(2024).astype(int)
        month = pd.to_numeric(raw["insp_month"], errors="coerce").fillna(1).astype(int).clip(1, 12)
        df["ship_date"] = pd.to_datetime(
            year.astype(str) + "-" + month.astype(str).str.zfill(2) + "-01",
            errors="coerce",
        )

        state = raw["carrier_phy_state"].fillna("Unknown")
        df["facility"]             = state
        df["OriginRegion"]         = state
        df["DestRegion"]           = "Unknown"
        df["origin_city"]          = state
        df["destination_city"]     = "Unknown"
        df["lane"]                 = state + " → Unknown"

        # Proxy numeric fields
        df["weight_lbs"]           = pd.to_numeric(
            raw["sms_nbr_power_unit"], errors="coerce"
        ).fillna(0) * 15  # rough proxy: power units × avg weight/unit

        df["miles"]                = pd.to_numeric(
            raw["carrier_mcs150_mileage"], errors="coerce"
        ).fillna(0).clip(0, 500000)

        # Risk fields — scale 0–100
        raw_score = pd.to_numeric(raw["accessorial_risk_score"], errors="coerce").fillna(0)
        score_max = raw_score.max() if raw_score.max() > 0 else 1
        df["risk_score"] = (raw_score / score_max * 100).clip(0, 100).round(1)

        def _tier(s):
            if s >= 75: return "High"
            if s >= 40: return "Medium"
            return "Low"
        df["risk_tier"] = df["risk_score"].apply(_tier)

        df["accessorial_charge_usd"] = df["risk_score"] * 12   # illustrative
        df["base_freight_usd"]       = df["miles"].clip(100, 5000) * 2.1
        df["total_cost_usd"]         = df["base_freight_usd"] + df["accessorial_charge_usd"]
        df["cost_per_mile"]          = (
            df["base_freight_usd"] / df["miles"].replace(0, float("nan"))
        ).fillna(0)

        df["AppointmentType"] = "Unknown"
        df["Revenue"]         = df["base_freight_usd"]
        df["AccessorialFlag"] = (df["risk_score"] >= 40).astype(int)

        return df

    except Exception:
        return pd.DataFrame()


def load_shipments_with_fallback(n_mock: int = 300) -> pd.DataFrame:
    """
    Load shipments with a three-tier fallback:
      1. Azure SQL  (live data)
      2. Teradata   (pace_synthetic_v training view)
      3. Mock data  (generated, n_mock rows)
    """
    # ── Tier 1: Azure SQL ─────────────────────────────────────────────
    conn = get_connection_safe()
    df = get_shipments(conn) if conn is not None else pd.DataFrame()
    if not df.empty:
        return df

    # ── Tier 2: Teradata ──────────────────────────────────────────────
    df = load_shipments_from_teradata()
    if not df.empty:
        st.info(
            f"Azure SQL unavailable — showing {len(df):,} records from Teradata.",
            icon="🗄️",
        )
        return df

    # ── Tier 3: Mock data ─────────────────────────────────────────────
    from utils.mock_data import generate_mock_shipments
    df = generate_mock_shipments(n_mock)
    st.info("Live database unavailable — showing demo data.", icon="ℹ️")
    return df


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


def ensure_model_results_table(_conn) -> None:
    """
    Create the ModelResults table if it does not already exist.

    Schema:
        result_id         INT IDENTITY PRIMARY KEY
        dot_number        VARCHAR(20)   — USDOT number (nullable for manual/batch inputs)
        run_timestamp     DATETIME      — UTC time of inference
        risk_score        FLOAT         — predicted risk score (0–100)
        risk_label        VARCHAR(20)   — Low / Medium / High / Critical / None
        charge_type       VARCHAR(50)   — predicted charge type label
        probabilities_json NVARCHAR(MAX) — JSON object of per-class probabilities
        input_source      VARCHAR(50)   — live_fmcsa / manual_input / csv_batch / etc.
    """
    if _conn is None:
        return
    ddl = """
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'ModelResults'
        )
        BEGIN
            CREATE TABLE ModelResults (
                result_id          INT IDENTITY(1,1) PRIMARY KEY,
                dot_number         VARCHAR(20)    NULL,
                run_timestamp      DATETIME       NOT NULL,
                risk_score         FLOAT          NOT NULL,
                risk_label         VARCHAR(20)    NOT NULL,
                charge_type        VARCHAR(50)    NOT NULL,
                probabilities_json NVARCHAR(MAX)  NULL,
                input_source       VARCHAR(50)    NOT NULL
            )
        END
    """
    try:
        cursor = _conn.cursor()
        cursor.execute(ddl)
        _conn.commit()
    except Exception:
        pass


def write_model_result(
    _conn,
    dot_number: str,
    run_timestamp,
    risk_score: float,
    risk_label: str,
    charge_type: str,
    probabilities_json: str,
    input_source: str,
) -> bool:
    """
    Insert one inference result into ModelResults.
    Silently returns False on failure so scoring is never blocked by a DB error.
    """
    if _conn is None:
        return False
    ensure_model_results_table(_conn)
    try:
        cursor = _conn.cursor()
        cursor.execute(
            """
            INSERT INTO ModelResults
                (dot_number, run_timestamp, risk_score, risk_label,
                 charge_type, probabilities_json, input_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (dot_number, run_timestamp, risk_score, risk_label,
             charge_type, probabilities_json, input_source),
        )
        _conn.commit()
        return True
    except Exception:
        return False


@st.cache_data(ttl=300)
def get_model_results(_conn, row_limit: int = 2000) -> pd.DataFrame:
    """Return recent ModelResults rows ordered by run_timestamp descending."""
    if _conn is None:
        return pd.DataFrame()
    query = f"""
        SELECT TOP {row_limit}
            result_id, dot_number, run_timestamp, risk_score,
            risk_label, charge_type, probabilities_json, input_source
        FROM ModelResults
        ORDER BY run_timestamp DESC
    """  # nosec B608
    try:
        return pd.read_sql(query, _conn)
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
    """  # nosec B608
    try:
        df = pd.read_sql(query, _conn)
        df["total_cost_usd"] = df["base_freight_usd"].fillna(0) + df["accessorial_charge_usd"].fillna(0)
        return df
    except Exception:
        return pd.DataFrame()
