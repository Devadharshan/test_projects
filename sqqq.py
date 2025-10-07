import os
import pandas as pd
import glob
import logging
import oracledb

# ---------------------------
# Setup Logging
# ---------------------------
log_file = "xls_crds_processing.log"
sql_log_file = "executed_queries.sql"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("===== Script started =====")

# ---------------------------
# Helper to log SQL
# ---------------------------
def log_sql(query):
    with open(sql_log_file, "a", encoding="utf-8") as f:
        f.write(query.strip() + ";\n\n")
    logging.info(f"SQL logged: {query.strip()}")

# ---------------------------
# Oracle Client Setup
# ---------------------------
try:
    oracledb.init_oracle_client(lib_dir=r"C:\path\to\instantclient_21_13")  # change this
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
# Function to read Excel safely with CSV fallback
# ---------------------------
def read_excel_as_df(file_path):
    try:
        df = pd.read_excel(file_path, dtype=str, engine="xlrd")  # xlrd works for .xls
        df.fillna("", inplace=True)
        return df
    except Exception as e:
        logging.warning(f"Failed to read {file_path} as Excel: {e}")
        try:
            csv_path = file_path.replace(".xls", ".csv")
            pd.read_excel(file_path, engine="xlrd").to_csv(csv_path, index=False)
            df = pd.read_csv(csv_path, dtype=str)
            df.fillna("", inplace=True)
            os.remove(csv_path)
            return df
        except Exception as e2:
            logging.error(f"Failed to convert {file_path} to CSV: {e2}")
            return None

# ---------------------------
# Folder Setup
# ---------------------------
folder_path = r"C:\path\to\your\xls_folder"  # change this
excel_files = glob.glob(os.path.join(folder_path, "*.xls"))

if not excel_files:
    logging.warning(f"No .xls files found in {folder_path}")
else:
    logging.info(f"Found {len(excel_files)} Excel files to process.")

# ---------------------------
# Extract CRDS codes
# ---------------------------
all_crds = set()

for file_path in excel_files:
    file_name = os.path.basename(file_path)
    df = read_excel_as_df(file_path)
    if df is None:
        logging.warning(f"Skipping {file_name}, cannot read.")
        continue

    crds_col = find_crds_column(df)
    if not crds_col:
        logging.warning(f"No CRDS column found in {file_name}")
        continue

    logging.info(f"✅ Found CRDS column '{crds_col}' in {file_name}")
    crds_values = df[crds_col].dropna().astype(str).str.strip().tolist()
    crds_values = [v for v in crds_values if v]

    all_crds.update(crds_values)
    logging.info(f"Extracted {len(crds_values)} CRDS codes from {file_name}")

if not all_crds:
    logging.warning("No CRDS values found in any file.")
else:
    logging.info(f"Total unique CRDS codes collected: {len(all_crds)}")

# ---------------------------
# Prepare IN clause safely
# ---------------------------
crds_list = list(all_crds)
# Oracle IN clause max 1000 items per batch; split if necessary
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# ---------------------------
# Run SELECT queries for each batch
# ---------------------------
queries_template = [
    "SELECT * FROM customer_table WHERE CRDS_CODE IN ({in_clause})",
    "SELECT COUNT(*) FROM transactions WHERE CRDS_CODE IN ({in_clause})",
    "SELECT CRDS_CODE, STATUS FROM accounts WHERE CRDS_CODE IN ({in_clause})",
    "SELECT DISTINCT REGION FROM crds_mapping WHERE CRDS_CODE IN ({in_clause})",
    "SELECT CRDS_CODE, LAST_UPDATED FROM audit_log WHERE CRDS_CODE IN ({in_clause})"
]

if crds_list:
    batch_size = 1000  # Oracle limit
    for batch in chunks(crds_list, batch_size):
        in_clause = ", ".join(f"'{c}'" for c in batch)
        for i, template in enumerate(queries_template, 1):
            query = template.format(in_clause=in_clause)
            try:
                cursor.execute(query)
                results = cursor.fetchall()
                logging.info(f"✅ Query {i} executed successfully ({len(results)} rows).")
                log_sql(query)
                for row in results[:5]:
                    logging.info(f"Result preview: {row}")
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
print(f"✅ Done. Logs: {os.path.abspath(log_file)} | SQL log: {os.path.abspath(sql_log_file)}")