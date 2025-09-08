import oracledb

# DSN for the database
host = "your_db_host"
port = 1521
service_name = "XEPDB1"
dsn = oracledb.makedsn(host, port, service_name=service_name)

# OS authentication
connection = oracledb.connect(dsn=dsn, mode=oracledb.SYSDBA)  # or just default mode

cursor = connection.cursor()
cursor.execute("SELECT sysdate FROM dual")
print("Current Date from DB:", cursor.fetchone()[0])

cursor.close()
connection.close()