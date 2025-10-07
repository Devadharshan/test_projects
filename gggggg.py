import os
import pandas as pd
import glob
import logging
import oracledb
from datetime import datetime

# ---------------------------
# Setup Logging
# ---------------------------
log_file = "xls_oracle_processing.log"
sql_log_file = "executed_queries.sql"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("===== Script started =====")

# Helper function to log SQLs
def log_sql(query):
    with open(sql_log_file, "a", encoding="utf-8") as f:
        f.write(query.strip() + ";\n")
    logging.info(f"SQL logged: {query.strip()}")

# ---------------------------
# Oracle Connection Setup
# ---------------------------
try:
    oracledb.init_oracle_client(lib_dir=r"C:\path\to\instantclient_21_13")  # 👈 change path
    conn = oracledb.connect(
        user="YOUR_USERNAME",
        password="YOUR_PASSWORD",
        dsn="hostname:port/servicename"
    )
    cursor = conn.cursor()
    logging.info("✅ Connected to Oracle database successfully.")
except Exception as e:
    logging.error(f"❌ Error connecting to Oracle: {e}")
    raise

# ---------------------------
# Function to detect CRDS column
# ---------------------------
def find_crds_column(df):
    possible_names = [
        "crds", "crds code", "crds_code", "crds codes",
        "crdscode", "crdsid", "crdsid code", "crds id"
    ]
    for col in df.columns:
        normalized = col.strip().lower().replace("_", " ").replace("-", " ")
        if any(name in normalized for name in possible_names):
            return col
    return None

# ---------------------------
# Folder Path Setup
# ---------------------------
folder_path = r"C:\path\to\your\xls_folder"  # 👈 change this
excel_files = glob.glob(os.path.join(folder_path, "*.xls"))

if not excel_files:
    logging.warning(f"No .xls files found in {folder_path}")
else:
    logging.info(f"Found {len(excel_files)} Excel files in {folder_path}")

# ---------------------------
# Process XLS Files
# ---------------------------
for file_path in excel_files:
    try:
        file_name = os.path.basename(file_path)
        logging.info(f"📄 Processing file: {file_name}")

        df = pd.read_excel(file_path, dtype=str)
        df.fillna("", inplace=True)

        crds_col = find_crds_column(df)
        if not crds_col:
            logging.warning(f"No CRDS-like column found in {file_name}")
            continue

        logging.info(f"✅ Found CRDS column '{crds_col}' in {file_name}")

        crds_values = df[crds_col].dropna().unique().tolist()
        logging.info(f"Extracted {len(crds_values)} unique CRDS values from {file_name}")

        # Insert CRDS codes to Oracle
        for val in crds_values:
            val = val.strip()
            if not val:
                continue

            insert_query = f"INSERT INTO your_table_name (CRDS_CODE, FILE_SOURCE, INSERTED_AT) VALUES ('{val}', '{file_name}', SYSDATE)"
            log_sql(insert_query)

            try:
                cursor.execute(insert_query)
            except Exception as e:
                logging.error(f"Insert failed for {val} in {file_name}: {e}")

        conn.commit()
        logging.info(f"💾 Data from {file_name} committed successfully.")

    except Exception as e:
        logging.error(f"❌ Error processing file {file_path}: {e}")

# ---------------------------
# Run 5 Select Queries
# ---------------------------
queries = [
    "SELECT COUNT(*) FROM your_table_name",
    "SELECT DISTINCT FILE_SOURCE FROM your_table_name",
    "SELECT CRDS_CODE FROM your_table_name WHERE ROWNUM <= 10",
    "SELECT CRDS_CODE, COUNT(*) AS OCCURRENCE FROM your_table_name GROUP BY CRDS_CODE HAVING COUNT(*) > 1",
    "SELECT * FROM your_table_name WHERE INSERTED_AT > SYSDATE - 1"
]

logging.info("Executing 5 SELECT queries...")
for i, query in enumerate(queries, 1):
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        logging.info(f"✅ Query {i} executed successfully: {query}")
        log_sql(query)

        # Print limited preview of results
        for row in results[:5]:
            logging.info(f"Result: {row}")

    except Exception as e:
        logging.error(f"❌ Error executing query {i}: {e}")

# ---------------------------
# Cleanup
# ---------------------------
try:
    cursor.close()
    conn.close()
    logging.info("🔒 Oracle connection closed.")
except Exception as e:
    logging.error(f"Error closing Oracle connection: {e}")

logging.info("===== Script completed =====")
print(f"✅ Completed. Logs: {os.path.abspath(log_file)} | SQL log: {os.path.abspath(sql_log_file)}")