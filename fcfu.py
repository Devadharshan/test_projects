import oracledb
import pandas as pd
import logging
from datetime import datetime
import os

# ========= Logging Setup =========
log_filename = f"oracle_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ========= Step 1: Folder setup =========
folder_path = r"C:\path\to\codes_files"  # adjust to your folder
excel_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.xls', '.xlsx'))]

if not excel_files:
    logging.warning(f"No Excel files found in {folder_path}. Exiting.")
    exit()

# ========= Step 2: Oracle DB Connection =========
oracledb.init_oracle_client(lib_dir=r"C:\path\to\instant_client")  # adjust if needed
conn = oracledb.connect(
    user="your_username",
    password="your_password",
    dsn="hostname:port/service_name"
)
cursor = conn.cursor()
logging.info("✅ Oracle DB connection established.")

# ========= Step 3: Define Queries (multi-line supported) =========
queries = [
    """
    SELECT 
        CASE WHEN code IN ({codes}) THEN 'Valid' ELSE 'Invalid' END as status,
        code
    FROM codes_table
    WHERE code IN ({codes})
    """,
    """
    SELECT COUNT(*) FROM employees WHERE code IN ({codes})
    """
    # Add more queries as needed
]

sql_output_file = "executed_queries.sql"
executed_sqls = []

# ========= Step 4: Process Each Excel File =========
for file in excel_files:
    file_path = os.path.join(folder_path, file)
    logging.info(f"\n========== Processing file: {file} ==========")
    print(f"Processing file: {file}")

    # Read Excel
    df = pd.read_excel(file_path)

    # Find all 'Codes' columns
    code_columns = [col for col in df.columns if "Codes" in str(col)]
    codes = set()
    for col in code_columns:
        codes.update(df[col].dropna().astype(str).tolist())
    codes = list(codes)

    if not codes:
        logging.warning(f"No codes found in file: {file}. Skipping.")
        continue

    # Prepare codes list for SQL
    codes_list = ",".join([f"'{c}'" for c in codes])

    # ========= Step 5: Execute Queries =========
    with open(sql_output_file, "a") as f:  # append to SQL file
        for idx, q in enumerate(queries, start=1):
            try:
                # Replace placeholder with real codes for logging and SQL file
                actual_sql = q.replace("{codes}", codes_list)
                executed_sqls.append(actual_sql)
                f.write(f"-- File: {file}\n")
                f.write(actual_sql + ";\n")

                # Prepare bind variables for execution
                placeholders = ",".join([f":c{i}" for i in range(len(codes))])
                bind_vars = {f"c{i}": code for i, code in enumerate(codes)}
                sql_with_placeholders = q.replace("{codes}", placeholders)

                # Execute query
                cursor.execute(sql_with_placeholders, bind_vars)
                result = cursor.fetchall()

                # Single-line summary log
                if result:
                    logging.info(f"File: {file} | Query {idx}: Data found ✅ ({len(result)} rows)")
                else:
                    logging.info(f"File: {file} | Query {idx}: No data found ⚠️ (0 rows)")

            except Exception as e:
                logging.error(f"File: {file} | Query {idx}: Execution failed ❌ - {e}")

# ========= Step 6: Close Connection =========
cursor.close()
conn.close()
logging.info("✅ Connection closed. All queries executed.")

# ========= Step 7: Print all executed SQL =========
print("\n========= Executed SQL Statements =========")
for sql in executed_sqls:
    print(sql + ";")