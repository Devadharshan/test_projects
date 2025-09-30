import os
import pandas as pd
import logging
import oracledb

# -------------------
# CONFIG
# -------------------
folder_path = r"codes_files"

oracle_config = {
    "user": "your_username",
    "password": "your_password",
    "dsn": "your_host:1521/your_service"  # e.g. "localhost:1521/XEPDB1"
}

# -------------------
# LOGGING
# -------------------
logging.basicConfig(
    filename="codes_processing.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------
# HELPERS
# -------------------
def normalize_columns(cols):
    """Normalize column names (case, spaces, etc.)"""
    normalized = []
    for c in cols:
        c = c.strip().lower()
        c = c.replace(" ", "")
        c = c.replace("-", "")
        normalized.append(c)
    return normalized

def read_file(file_path):
    """Read Excel or HTML file into DataFrame"""
    try:
        if file_path.endswith(".xls"):
            df = pd.read_excel(file_path, engine="xlrd", dtype=str)
        elif file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path, engine="openpyxl", dtype=str)
        elif file_path.endswith(".html") or file_path.endswith(".htm"):
            df_list = pd.read_html(file_path)
            df = df_list[0]
        else:
            logging.warning(f"Skipping unsupported file format: {file_path}")
            return None

        # Normalize column names
        df.columns = normalize_columns(df.columns)
        return df
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return None

# -------------------
# MAIN
# -------------------
try:
    conn = oracledb.connect(**oracle_config)
    cur = conn.cursor()
    logging.info("Connected to Oracle DB successfully")
except Exception as e:
    logging.error(f"DB connection failed: {e}")
    raise

for file in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file)
    logging.info(f"Processing file: {file_path}")
    df = read_file(file_path)

    if df is None:
        continue

    # Look for CRDS codes/CRDS code variations
    code_col = None
    for col in df.columns:
        if "crdscode" in col or "crdscodes" in col:
            code_col = col
            break

    if code_col is None:
        logging.warning(f"No CRDS code(s) column found in {file}")
        continue

    codes = df[code_col].dropna().unique().tolist()
    logging.info(f"Found {len(codes)} codes in {file}")

    for idx, code in enumerate(codes, start=1):
        sql = f"""
        SELECT * 
        FROM my_table 
        WHERE code = '{code}'
        """
        sql = " ".join(sql.split())  # flatten into one line
        try:
            cur.execute(sql)
            result = cur.fetchall()
            if result:
                logging.info(f"File {file} | Query {idx}: FOUND for code {code} | SQL: {sql}")
            else:
                logging.info(f"File {file} | Query {idx}: NOT FOUND for code {code} | SQL: {sql}")
        except Exception as e:
            logging.error(f"File {file} | Query {idx}: ERROR for code {code} | {e} | SQL: {sql}")

cur.close()
conn.close()
logging.info("All files processed, DB connection closed")