import os
import pandas as pd
import oracledb
import logging
from datetime import datetime

# ========= Logging Setup =========
log_filename = f"oracle_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ========= Step 1: Folder with files =========
folder_path = "codes_files"

# List all .xls files
xls_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".xls")]

if not xls_files:
    logging.warning("⚠️ No .xls files found in codes_files folder. Exiting.")
    exit()

# ========= Step 2: Oracle DB Connection =========
try:
    oracledb.init_oracle_client(lib_dir=r"C:\path\to\instant_client")  # Adjust path
    conn = oracledb.connect(
        user="your_username",
        password="your_password",
        dsn="hostname:port/service_name"
    )
    cursor = conn.cursor()
    logging.info("✅ Oracle DB connection established.")
except Exception as e:
    logging.error(f"❌ Failed to connect to Oracle DB: {e}")
    exit()

# ========= Step 3: Define Queries =========
queries = [
    "SELECT * FROM codes_table WHERE code IN ({codes})",
    "SELECT COUNT(*) FROM employees WHERE code IN ({codes})",
    "SELECT code, status FROM orders WHERE code IN ({codes})",
    "SELECT DISTINCT region FROM customers WHERE code IN ({codes})",
    "SELECT code, SUM(amount) FROM transactions WHERE code IN ({codes}) GROUP BY code"
]

# ========= Step 4: Process each file =========
sql_output_file = f"executed_queries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
executed_sqls = []

with open(sql_output_file, "w", encoding="utf-8") as f:  # write SQL file
    for file_name in xls_files:
        file_path = os.path.join(folder_path, file_name)
        logging.info(f"📂 Processing file: {file_name}")
        print(f"Processing file: {file_name}")

        try:
            # Read HTML disguised Excel with latin1 encoding
            with open(file_path, "r", encoding="latin1") as f_in:
                df_list = pd.read_html(f_in)
            df = df_list[0]

            # Normalize column names: lowercase + remove spaces
            df.columns = [str(c).strip().lower().replace(" ", "") for c in df.columns]

            # Find columns that contain both 'crds' and 'code'
            code_columns = [col for col in df.columns if "crds" in col and "code" in col]

            # Collect all unique codes
            codes = set()
            for col in code_columns:
                codes.update(df[col].dropna().astype(str).tolist())
            codes = list(codes)

            if not codes:
                logging.warning(f"⚠️ No Crds codes found in file {file_name}. Skipping.")
                continue

            # Prepare codes list for SQL IN clause
            codes_list = ",".join([f"'{c}'" for c in codes])

            # Execute queries
            for idx, q in enumerate(queries, start=1):
                try:
                    actual_sql = q.replace("{codes}", codes_list)
                    executed_sqls.append(actual_sql)
                    f.write(f"-- From file: {file_name}\n{actual_sql};\n\n")

                    # Bind placeholders for safe execution
                    placeholders = ",".join([f":c{i}" for i in range(len(codes))])
                    bind_vars = {f"c{i}": code for i, code in enumerate(codes)}
                    sql_with_placeholders = q.replace("{codes}", placeholders)

                    # Execute query
                    cursor.execute(sql_with_placeholders, bind_vars)
                    result = cursor.fetchall()

                    # Log summary
                    row_count = len(result)
                    if row_count > 0:
                        logging.info(f"{file_name} | Query {idx}: ✅ Data found ({row_count} rows)")
                        print(f"{file_name} | Query {idx}: ✅ Data found ({row_count} rows)")
                    else:
                        logging.info(f"{file_name} | Query {idx}: ⚠️ No data found")
                        print(f"{file_name} | Query {idx}: ⚠️ No data found")

                except Exception as qe:
                    logging.error(f"{file_name} | Query {idx}: ❌ Failed - {qe}")
                    print(f"{file_name} | Query {idx}: ❌ Failed - {qe}")

        except Exception as fe:
            logging.error(f"❌ Failed to process file {file_name}: {fe}")
            print(f"❌ Failed to process file {file_name}: {fe}")

# ========= Step 5: Close Oracle Connection =========
cursor.close()
conn.close()
logging.info("✅ Connection closed. All queries executed.")

# ========= Step 6: Print all executed SQL =========
print("\n========= Executed SQL Statements =========")
for sql in executed_sqls:
    print(sql + ";")