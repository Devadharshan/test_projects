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
    "dsn": "host:1521/service"
}
queries = [
    "SELECT * FROM my_table WHERE code = '{code}'",
    "SELECT COUNT(*) FROM employees WHERE code = '{code}'"
]

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
def normalize_text(x):
    """Lowercase, remove spaces, convert to string"""
    return str(x).strip().lower().replace(" ", "")

def detect_code_column(df):
    """Find the column index where header contains 'crds' and 'code'"""
    for i, col in enumerate(df.iloc[0]):  # first row as candidate header
        if "crds" in normalize_text(col) and "code" in normalize_text(col):
            return i
    return None

def read_table(file_path):
    """Read HTML or Excel table as dataframe with header=None"""
    try:
        # Try Excel first
        if file_path.endswith(".xls") or file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path, header=None, dtype=str)
        else:  # HTML
            df_list = pd.read_html(file_path)
            df = df_list[0]

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
    logging.info("Connected to Oracle DB")
except Exception as e:
    logging.error(f"DB connection failed: {e}")
    raise

for fname in os.listdir(folder_path):
    file_path = os.path.join(folder_path, fname)
    logging.info(f"Processing file: {file_path}")
    df = read_table(file_path)
    if df is None or df.empty:
        continue

    code_col_idx = detect_code_column(df)
    if code_col_idx is None:
        logging.warning(f"No CRDS code column found in {fname}")
        continue

    # Use first row as header
    df.columns = [normalize_text(x) for x in df.iloc[0]]
    df = df[1:]  # drop header row
    codes = df.iloc[:, code_col_idx].dropna().unique().tolist()
    logging.info(f"Found {len(codes)} codes in {fname}: {codes[:10]}")

    # Execute queries for each code
    for idx, code in enumerate(codes, start=1):
        for qidx, q in enumerate(queries, start=1):
            sql = q.format(code=code)
            sql_one_line = " ".join(sql.split())  # flatten
            try:
                cur.execute(sql_one_line)
                result = cur.fetchall()
                if result:
                    logging.info(f"{fname} | Query {qidx} | Code {code}: FOUND")
                else:
                    logging.info(f"{fname} | Query {qidx} | Code {code}: NOT FOUND")
            except Exception as e:
                logging.error(f"{fname} | Query {qidx} | Code {code}: ERROR {e}")

cur.close()
conn.close()
logging.info("Processing completed, connection closed")