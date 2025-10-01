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
    "dsn": "host:1521/service"  # e.g. localhost:1521/XEPDB1
}

# Define your queries
# Use {codes} as placeholder → will be replaced with IN ('c1','c2',...)
queries = [
    "SELECT * FROM my_table WHERE code IN ({codes})",
    "SELECT COUNT(*) FROM employees WHERE code IN ({codes})"
]

# -------------------
# LOGGING
# -------------------
logging.basicConfig(
    filename="codes_processing.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

sql_outfile = "executed_queries.sql"

# -------------------
# HELPERS
# -------------------
def normalize_text(x):
    """Lowercase, remove spaces, convert to string"""
    return str(x).strip().lower().replace(" ", "")

def read_table(file_path):
    """Read Excel or HTML table without assuming header"""
    try:
        if file_path.endswith(".xls") or file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path, header=None, dtype=str)
        else:
            df_list = pd.read_html(file_path)
            df = df_list[0]
        return df
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return None

def detect_code_column(df):
    """Detect column index that looks like CRDS code(s)"""
    for i, col in enumerate(df.iloc[0]):  # first row as header
        norm = normalize_text(col)
        if "crds" in norm and "code" in norm:  # matches code / codes
            return i
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

with open(sql_outfile, "w") as sql_file:

    for fname in os.listdir(folder_path):
        file_path = os.path.join(folder_path, fname)
        logging.info(f"Processing file: {file_path}")
        df = read_table(file_path)
        if df is None or df.empty:
            continue

        code_col_idx = detect_code_column(df)
        if code_col_idx is None:
            logging.warning(f"No CRDS code(s) column found in {fname}")
            continue

        # Use first row as header
        df.columns = [normalize_text(x) for x in df.iloc[0]]
        df = df[1:]  # drop header row

        # Extract codes
        codes = df.iloc[:, code_col_idx].dropna().unique().tolist()
        if not codes:
            logging.info(f"No codes found in {fname}")
            continue

        # Format codes for SQL IN clause
        code_list = ", ".join(f"'{c}'" for c in codes)

        for qidx, q in enumerate(queries, start=1):
            sql = q.format(codes=code_list)
            sql_one_line = " ".join(sql.split())
            sql_file.write(sql_one_line + ";\n")

            try:
                cur.execute(sql_one_line)
                result = cur.fetchall()
                if result:
                    logging.info(f"{fname} | Query {qidx}: FOUND rows ({len(result)})")
                else:
                    logging.info(f"{fname} | Query {qidx}: NOT FOUND")
            except Exception as e:
                logging.error(f"{fname} | Query {qidx}: ERROR {e}")

cur.close()
conn.close()
logging.info("Processing completed, connection closed")