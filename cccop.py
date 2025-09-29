import oracledb
import pandas as pd
import logging
from datetime import datetime

# ========= Logging Setup =========
log_filename = f"oracle_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ========= Step 1: Read Excel =========
excel_file = "your_file.xlsx"
df = pd.read_excel(excel_file)

# Find all columns containing "Codes"
code_columns = [col for col in df.columns if "Codes" in str(col)]
logging.info(f"Detected code columns: {code_columns}")

# Extract all unique codes from those columns
codes = set()
for col in code_columns:
    codes.update(df[col].dropna().astype(str).tolist())

codes = list(codes)
logging.info(f"Extracted {len(codes)} unique codes: {codes}")

if not codes:
    logging.warning("No codes found in Excel. Exiting.")
    exit()

# ========= Step 2: Oracle DB Connection =========
try:
    oracledb.init_oracle_client(lib_dir=r"C:\path\to\instant_client")  # adjust for your setup
    conn = oracledb.connect(
        user="your_username",
        password="your_password",
        dsn="hostname:port/service_name"
    )
    cursor = conn.cursor()
    logging.info("✅ Oracle DB connection established.")
except Exception as e:
    logging.error(f"❌ Failed to connect to Oracle DB: {e}")
    raise

# ========= Step 3: Build Queries =========
queries = [
    "SELECT COUNT(*) FROM employees WHERE code IN ({codes})",
    "SELECT * FROM departments WHERE code IN ({codes})",
    "SELECT * FROM projects WHERE code IN ({codes})",
    "SELECT SUM(amount) FROM transactions WHERE code IN ({codes})",
    "SELECT status, code FROM codes_table WHERE code IN ({codes})"
]

# Create bind placeholders for all codes
placeholders = ",".join([f":c{i}" for i in range(len(codes))])
bind_vars = {f"c{i}": code for i, code in enumerate(codes)}

# ========= Step 4: Run Queries =========
sql_output_file = "executed_queries.sql"
executed_sqls = []

with open(sql_output_file, "w") as f:
    for q in queries:
        try:
            # SQL with placeholders
            sql = q.format(codes=placeholders)

            # SQL with real values (for logging & saving)
            actual_sql = q.format(codes=",".join([f"'{c}'" for c in codes]))
            executed_sqls.append(actual_sql)
            f.write(actual_sql + ";\n")

            # Execute query with bind variables
            cursor.execute(sql, bind_vars)
            result = cursor.fetchall()

            if result:
                logging.info(f"✅ Data found for query: {q}\nResult count: {len(result)}")
            else:
                logging.info(f"⚠️ No data found for query: {q}")

        except Exception as e:
            logging.error(f"❌ Failed to execute query [{q}]: {e}")

# ========= Step 5: Close =========
cursor.close()
conn.close()
logging.info("✅ Connection closed. All queries executed.")

# ========= Step 6: Print all SQL executed =========
print("\n========= Executed SQL Statements =========")
for sql in executed_sqls:
    print(sql + ";")