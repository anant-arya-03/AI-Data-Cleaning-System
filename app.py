import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import mysql.connector

st.set_page_config(page_title="MySQL Data Cleaner", layout="wide")
st.title("MySQL Data Cleaning Web App (Improved Detection)")

# --- CONNECT TO MYSQL ---
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="9873529883@Anant",   # <-- your password
        database="data_cleaning_system"
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customer_data;")
    rows = cursor.fetchall()
    df = pd.DataFrame(rows)
    st.success("Connected to MySQL and loaded data!")
except Exception as e:
    st.error("❌ Could not connect to MySQL")
    st.write(e)
    st.stop()

# ensure columns exist and correct dtypes
if "age" in df.columns:
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
if "salary" in df.columns:
    df["salary"] = pd.to_numeric(df["salary"], errors="coerce")

# --- SHOW ORIGINAL DATA ---
st.subheader("Original Data")
st.dataframe(df)

# --- MISSING VALUES ---
st.subheader("Missing Values")
st.write(df.isnull().sum())

# --- DUPLICATE DETECTION ---
st.subheader("Duplicate Detection")
# By default exclude id from duplicate detection if present
possible_cols = [c for c in df.columns if c != "id"]
st.write("Choose columns to consider when finding duplicates (default: name, email, age, salary)")
default_cols = [c for c in ["name", "email", "age", "salary"] if c in df.columns]
dup_cols = st.multiselect("Duplicate columns", options=possible_cols, default=default_cols)

if len(dup_cols) == 0:
    st.warning("Select at least one column to detect duplicates.")
else:
    dup_mask = df.duplicated(subset=dup_cols, keep=False)
    duplicates = df[dup_mask].sort_values(by=dup_cols)
    st.write(f"Total duplicate rows (based on {dup_cols}): {len(duplicates)}")
    if not duplicates.empty:
        st.dataframe(duplicates)
    else:
        st.write("No duplicates found using the selected columns.")

# --- ANOMALY DETECTION ---
st.subheader("Anomaly Detection (IsolationForest)")
num_cols = [c for c in ["age","salary"] if c in df.columns]
if len(num_cols) < 1:
    st.warning("No numeric columns (age, salary) available for anomaly detection.")
else:
    contamination = st.slider("Contamination (expected fraction of anomalies)", 0.01, 0.5, 0.1, 0.01)
    # Prepare numeric data: fill missing with column mean, scale
    numeric = df[num_cols].astype(float).copy()
    numeric_filled = numeric.fillna(numeric.mean())
    scaler = StandardScaler()
    numeric_scaled = scaler.fit_transform(numeric_filled)

    model = IsolationForest(contamination=float(contamination), random_state=42)
    preds = model.fit_predict(numeric_scaled)  # -1 anomaly, 1 normal
    df["_anomaly_flag"] = preds
    anomalies = df[df["_anomaly_flag"] == -1]
    st.write(f"Anomalies found: {len(anomalies)}")
    if not anomalies.empty:
        st.dataframe(anomalies)

# --- CLEANING OPTIONS & APPLY ---
st.subheader("Cleaning Options")
remove_dup = st.checkbox("Remove duplicates (based on selected columns)", value=True)
fill_email = st.checkbox("Fill missing emails with 'unknown@gmail.com'", value=True)
fill_age = st.checkbox("Fill missing ages with mean", value=True)
remove_anom = st.checkbox("Remove anomaly rows", value=False)

if st.button("Apply cleaning"):
    clean = df.copy()
    # remove duplicates using selected columns (keeps first occurrence)
    if remove_dup and len(dup_cols) > 0:
        clean = clean.drop_duplicates(subset=dup_cols, keep="first").reset_index(drop=True)
    # fill email
    if "email" in clean.columns and fill_email:
        clean["email"] = clean["email"].fillna("unknown@gmail.com")
    # fill age
    if "age" in clean.columns and fill_age:
        clean["age"] = clean["age"].fillna(clean["age"].mean())
    # remove anomalies if selected
    if remove_anom and "_anomaly_flag" in clean.columns:
        clean = clean[clean["_anomaly_flag"] != -1].copy()
        clean = clean.drop(columns=["_anomaly_flag"])
    else:
        if "_anomaly_flag" in clean.columns:
            clean = clean.drop(columns=["_anomaly_flag"])

    st.success("Cleaning applied — preview below")
    st.dataframe(clean)

    # offer save and download
    if st.checkbox("Save cleaned data to MySQL (replace table cleaned_customer_data)"):
        try:
            cursor.execute("DROP TABLE IF EXISTS cleaned_customer_data;")
            create_q = """
            CREATE TABLE cleaned_customer_data (
                id INT,
                name VARCHAR(100),
                email VARCHAR(200),
                age FLOAT,
                salary FLOAT
            );
            """
            cursor.execute(create_q)
            insert_q = "INSERT INTO cleaned_customer_data (id, name, email, age, salary) VALUES (%s,%s,%s,%s,%s);"
            # ensure columns order
            cols = ["id","name","email","age","salary"]
            for _, r in clean.iterrows():
                values = tuple((r[c] if c in r.index else None) for c in cols)
                cursor.execute(insert_q, values)
            conn.commit()
            st.success("Cleaned data saved to MySQL table cleaned_customer_data")
        except Exception as e:
            st.error(f"Failed to save cleaned data: {e}")

    st.download_button(
        "Download cleaned CSV",
        data=clean.to_csv(index=False).encode("utf-8"),
        file_name="cleaned_customer_data.csv",
        mime="text/csv"
    )
