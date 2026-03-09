import streamlit as st

import pandas as pd

import pyodbc



# -------------------------------------------------------------------

# Direct Azure SQL connection (same style as ml_pipeline.py)

# -------------------------------------------------------------------

DB_SERVER = "essql1.database.windows.net"

DB_NAME = "ISYS43603_Spring2026_Sec02_Alice_db"

DB_USERNAME = "Alice"

DB_PASSWORD = "ISYSPass12345678!"

DB_DRIVER = "ODBC Driver 18 for SQL Server"





def get_connection():

    conn_str = (

        f"DRIVER={{{DB_DRIVER}}};"

        f"SERVER=tcp:{DB_SERVER},1433;"

        f"DATABASE={DB_NAME};"

        f"UID={DB_USERNAME};"

        f"PWD={DB_PASSWORD};"

        "Encrypt=yes;"

        "TrustServerCertificate=no;"

        "Connection Timeout=30;"

    )

    return pyodbc.connect(conn_str)





st.set_page_config(

    page_title="PACE — Accessorial Tracker",

    page_icon="🚨",

    layout="wide"

)



st.title("🚨 Accessorial Risk Tracker")

st.caption("Review shipment risk predictions, explanations, and recommended actions.")



try:

    conn = get_connection()

except Exception as e:

    st.error(f"Database connection failed: {e}")

    st.stop()



query = """

    SELECT TOP 500

        ShipmentId,

        ShipDate,

        OriginRegion,

        DestRegion,

        AppointmentType,

        DistanceMiles,

        weight_lbs,

        risk_score,

        risk_tier,

        risk_reason,

        recommended_action

    FROM Shipments

    ORDER BY ShipmentId DESC

"""



try:

    df = pd.read_sql(query, conn)

except Exception as e:

    st.error(f"Failed to load shipment data: {e}")

    st.stop()

finally:

    conn.close()



if df.empty:

    st.warning("No shipment prediction data found.")

    st.stop()



# -----------------------------

# Sidebar filters

# -----------------------------

st.sidebar.header("Filters")



tier_options = ["All"] + sorted(df["risk_tier"].dropna().astype(str).unique().tolist())

selected_tier = st.sidebar.selectbox("Risk Tier", tier_options)



min_score = float(df["risk_score"].min()) if df["risk_score"].notna().any() else 0.0

max_score = float(df["risk_score"].max()) if df["risk_score"].notna().any() else 1.0



score_range = st.sidebar.slider(

    "Risk Score Range",

    min_value=0.0,

    max_value=1.0,

    value=(max(0.0, min_score), min(1.0, max_score)),

    step=0.01

)



search_id = st.sidebar.text_input("Search Shipment ID")



filtered_df = df.copy()



if selected_tier != "All":

    filtered_df = filtered_df[filtered_df["risk_tier"].astype(str) == selected_tier]



filtered_df = filtered_df[

    (filtered_df["risk_score"] >= score_range[0]) &

    (filtered_df["risk_score"] <= score_range[1])

]



if search_id.strip():

    filtered_df = filtered_df[

        filtered_df["ShipmentId"].astype(str).str.contains(search_id.strip(), na=False)

    ]



# -----------------------------

# KPI row

# -----------------------------

col1, col2, col3, col4 = st.columns(4)



col1.metric("Total Shipments", len(filtered_df))



high_count = int((filtered_df["risk_tier"].astype(str) == "High").sum())

medium_count = int((filtered_df["risk_tier"].astype(str) == "Medium").sum())

avg_score = filtered_df["risk_score"].mean() if not filtered_df.empty else 0



col2.metric("High Risk", high_count)

col3.metric("Medium Risk", medium_count)

col4.metric("Avg Risk Score", f"{avg_score:.2f}")



st.divider()



# -----------------------------

# Shipment cards

# -----------------------------

st.subheader("Shipment Risk Details")



if filtered_df.empty:

    st.info("No shipments match the selected filters.")

else:

    for _, row in filtered_df.iterrows():

        tier = str(row.get("risk_tier", "Unknown"))

        score = row.get("risk_score", 0)

        shipment_id = row.get("ShipmentId", "")

        ship_date = row.get("ShipDate", "")

        origin = row.get("OriginRegion", "")

        dest = row.get("DestRegion", "")

        appointment_type = row.get("AppointmentType", "")

        distance = row.get("DistanceMiles", "")

        weight = row.get("weight_lbs", "")

        reason = row.get("risk_reason", "")

        action = row.get("recommended_action", "")



        if tier == "High":

            badge = "🔴 High"

        elif tier == "Medium":

            badge = "🟠 Medium"

        else:

            badge = "🟢 Low"



        with st.container():

            st.markdown(f"### Shipment #{shipment_id} — {badge}")



            info_col1, info_col2, info_col3 = st.columns(3)



            info_col1.write(f"**Ship Date:** {ship_date}")

            info_col1.write(f"**Appointment Type:** {appointment_type}")



            info_col2.write(f"**Origin → Destination:** {origin} → {dest}")

            info_col2.write(f"**Distance (miles):** {distance}")



            info_col3.write(f"**Weight (lbs):** {weight}")

            info_col3.write(f"**Risk Score:** {score:.3f}")



            st.markdown("**Why this shipment is risky**")

            st.info(

                reason if pd.notna(reason) and str(reason).strip()

                else "No explanation available."

            )



            st.markdown("**Recommended action**")

            st.success(

                action if pd.notna(action) and str(action).strip()

                else "No recommendation available."

            )



            st.divider()