import os
import pandas as pd
import glob
import logging
import oracledb
from datetime import datetime

# ---------------------------
# Setup Logging
# ---------------------------
log_file = "xls_crds_query.log"
sql_log_file = "executed_queries.sql"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("===== Script started =====")

# Helper to log SQL
def log_sql(query):
    with open(sql_log_file, "a", encoding="utf-8") as f:
        f.write(query.strip() + ";\n\n")
    logging.info(f"SQL logged: {query.strip()}")

# ---------------------------
# Oracle Client Setup
# ---------------------------
try:
    oracledb.init_oracle_client(lib_dir=r"C:\path\to\instantclient_21_13")  # 👈 change this
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
# Detect CRDS Column
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
# Folder Setup
# ---------------------------
folder_path = r"C:\path\to\your\xls_folder"  # 👈 change this
excel_files = glob.glob(os.path.join(folder_path, "*.xls"))

if not excel_files:
    logging.warning(f"No .xls files found in {folder_path}")
else:
    logging.info(f"Found {len(excel_files)} Excel files to process.")

# ---------------------------
# Extract all CRDS codes from all files
# ---------------------------
all_crds = set()

for file_path in excel_files:
    try:
        file_name = os.path.basename(file_path)
        logging.info(f"📄 Reading file: {file_name}")

        df = pd.read_excel(file_path, dtype=str)
        df.fillna("", inplace=True)

        crds_col = find_crds_column(df)
        if not crds_col:
            logging.warning(f"No CRDS column found in {file_name}")
            continue

        logging.info(f"✅ Found CRDS column '{crds_col}' in {file_name}")
        crds_values = df[crds_col].dropna().astype(str).str.strip().tolist()
        crds_values = [val for val in crds_values if val]

        all_crds.update(crds_values)
        logging.info(f"Extracted {len(crds_values)} CRDS codes from {file_name}")
    except Exception as e:
        logging.error(f"❌ Error processing {file_path}: {e}")

if not all_crds:
    logging.warning("No CRDS values found in any file.")
else:
    logging.info(f"Total unique CRDS codes collected: {len(all_crds)}")

# ---------------------------
# Prepare CRDS list for SQL IN clause
# ---------------------------
crds_list = list(all_crds)
if len(crds_list) > 1000:
    crds_list = crds_list[:1000]  # Oracle limit for demo; adjust as needed
in_clause = ", ".join(f"'{c}'" for c in crds_list)

# ---------------------------
# Run 5 SQL Queries using CRDS codes
# ---------------------------
queries = [
    f"SELECT * FROM customer_table WHERE CRDS_CODE IN ({in_clause})",
    f"SELECT COUNT(*) FROM transactions WHERE CRDS_CODE IN ({in_clause})",
    f"SELECT CRDS_CODE, STATUS FROM accounts WHERE CRDS_CODE IN ({in_clause})",
    f"SELECT DISTINCT REGION FROM crds_mapping WHERE CRDS_CODE IN ({in_clause})",
    f"SELECT CRDS_CODE, LAST_UPDATED FROM audit_log WHERE CRDS_CODE IN ({in_clause})"
]

logging.info("Executing 5 CRDS-based SELECT queries...")

for i, query in enumerate(queries, 1):
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        logging.info(f"✅ Query {i} executed successfully ({len(results)} rows).")
        log_sql(query)
        # Print limited preview to logs
        for row in results[:5]:
            logging.info(f"Result: {row}")
    except Exception as e:
        logging.error(f"❌ Error executing query {i}: {e}")
        log_sql(f"-- FAILED: {query}")

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
print(f"✅ Done. Log: {os.path.abspath(log_file)} | SQL log: {os.path.abspath(sql_log_file)}")