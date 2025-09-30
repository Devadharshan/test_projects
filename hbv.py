import os
import pandas as pd
import logging
import sqlite3  # You can switch to cx_Oracle if connecting to Oracle

# Configure logging
logging.basicConfig(
    filename="codes_processing.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Folder where .xls or .html files are present
folder_path = r"codes_files"

# Function to normalize column names
def normalize_columns(cols):
    normalized = []
    for c in cols:
        c = c.strip().lower()              # lowercase + strip spaces
        c = c.replace(" ", "")             # remove spaces
        c = c.replace("-", "")             # remove hyphens if any
        normalized.append(c)
    return normalized

# Function to read a file (xls or html)
def read_file(file_path):
    try:
        if file_path.endswith(".xls") or file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path, header=0, dtype=str)
        elif file_path.endswith(".html") or file_path.endswith(".htm"):
            df_list = pd.read_html(file_path)
            df = df_list[0]  # take first table
        else:
            logging.warning(f"Skipping unsupported file format: {file_path}")
            return None

        # Normalize column names
        df.columns = normalize_columns(df.columns)
        return df
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return None

# Process each file
for file in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file)
    logging.info(f"Processing file: {file_path}")
    df = read_file(file_path)

    if df is None:
        continue

    # Look for CRDS codes column (covers "crds code", "crds codes", etc.)
    code_col = None
    for col in df.columns:
        if "crdscode" in col:   # matches crdscode / crdscodes
            code_col = col
            break

    if code_col is None:
        logging.warning(f"No CRDS code(s) column found in {file}")
        continue

    codes = df[code_col].dropna().unique().tolist()
    logging.info(f"Found {len(codes)} codes in {file}")

    # Example SQL execution
    conn = sqlite3.connect(":memory:")  # Replace with your Oracle connection
    cur = conn.cursor()

    for idx, code in enumerate(codes, start=1):
        sql = f"SELECT * FROM my_table WHERE code = '{code}'"
        try:
            cur.execute(sql)
            result = cur.fetchall()
            if result:
                logging.info(f"Query {idx}: Found for code {code} | SQL: {sql}")
            else:
                logging.info(f"Query {idx}: Not found for code {code} | SQL: {sql}")
        except Exception as e:
            logging.error(f"Error executing query for {code}: {e} | SQL: {sql}")

    conn.close()