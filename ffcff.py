import os
import pandas as pd
import glob
import logging
import oracledb

# ---------------------------
# Setup Logging
# ---------------------------
log_file = "xls_to_oracle.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("===== Script started =====")

# ---------------------------
# Oracle Client Setup
# ---------------------------
try:
    oracledb.init_oracle_client(lib_dir=r"C:\path\to\instantclient_21_13")  # Update your path
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
# Function to find CRDS code column
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
    logging.info(f"Found {len(excel_files)} Excel files to process in {folder_path}")

# ---------------------------
# Process Each File
# ---------------------------
for file_path in excel_files:
    try:
        file_name = os.path.basename(file_path)
        logging.info(f"📄 Processing file: {file_name}")

        # Read Excel (as string to avoid dtype issues)
        df = pd.read_excel(file_path, dtype=str)
        df.fillna("", inplace=True)

        # Find CRDS column
        crds_col = find_crds_column(df)
        if not crds_col:
            logging.warning(f"No CRDS-like column found in {file_name}")
            continue

        logging.info(f"✅ Found CRDS column '{crds_col}' in {file_name}")

        # Extract unique CRDS values
        crds_values = df[crds_col].dropna().unique().tolist()
        logging.info(f"Extracted {len(crds_values)} unique CRDS values from {file_name}")

        # Insert into Oracle (example)
        for val in crds_values:
            if val.strip():
                try:
                    cursor.execute("INSERT INTO your_table_name (CRDS_CODE) VALUES (:1)", [val])
                except Exception as e:
                    logging.error(f"Failed to insert value '{val}' from {file_name}: {e}")

        conn.commit()
        logging.info(f"💾 Data from {file_name} committed to Oracle successfully.")

    except Exception as e:
        logging.error(f"❌ Error processing file {file_path}: {e}")

# ---------------------------
# Cleanup
# ---------------------------
try:
    cursor.close()
    conn.close()
    logging.info("🔒 Oracle connection closed.")
except Exception as e:
    logging.error(f"Error closing connection: {e}")

logging.info("===== Script completed =====")
print(f"✅ Processing complete. Check log file: {os.path.abspath(log_file)}")