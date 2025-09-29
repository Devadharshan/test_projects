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

# ========= Step 3: Queries =========
queries = [
    "SELECT COUNT(*) FROM employees WHERE code = :code",
    "SELECT * FROM departments WHERE code = :code",
    "SELECT * FROM projects WHERE code = :code",
    "SELECT SUM(amount) FROM transactions WHERE code = :code",
    "SELECT status FROM codes_table WHERE code = :code"
]

# ========= Step 4: Run Queries =========
sql_output_file = "executed_queries.sql"

with open(sql_output_file, "w") as f:
    for code in codes:
        logging.info(f"Running queries for code: {code}")
        for q in queries:
            try:
                # Save the actual SQL with substituted value
                actual_sql = q.replace(":code", f"'{code}'")
                f.write(actual_sql + ";\n")

                cursor.execute(q, {"code": code})
                result = cursor.fetchall()

                if result:
                    logging.info(f"✅ Data found for query [{q}] with code [{code}] → {result}")
                else:
                    logging.info(f"⚠️ No data found for query [{q}] with code [{code}]")

            except Exception as e:
                logging.error(f"❌ Failed to execute query [{q}] with code [{code}]: {e}")

# ========= Step 5: Close =========
cursor.close()
conn.close()
logging.info("✅ Connection closed. All queries executed.")