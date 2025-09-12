import cx_Oracle

# Replace with your details
username = "your_username"
password = "your_password"
dsn = "hostname:1521/servicename"  # e.g., "localhost:1521/ORCLPDB1"

try:
    # Connect to Oracle DB
    connection = cx_Oracle.connect(username, password, dsn)
    print("✅ Connected to Oracle Database")

    cursor = connection.cursor()

    # Query to check blocking sessions
    blocking_query = """
    SELECT 
        s1.sid || ',' || s1.serial# AS blocker,
        s1.username AS blocker_user,
        s2.sid || ',' || s2.serial# AS blocked,
        s2.username AS blocked_user,
        s1.sql_id AS blocker_sql,
        s2.sql_id AS blocked_sql
    FROM gv$session s1
    JOIN gv$session s2 ON s1.sid = s2.blocking_session
    """

    cursor.execute(blocking_query)
    results = cursor.fetchall()

    if results:
        print("\n🔒 Blocking Sessions Found:")
        for row in results:
            print(f"Blocker: {row[0]} ({row[1]}), "
                  f"Blocked: {row[2]} ({row[3]}), "
                  f"Blocker SQL: {row[4]}, Blocked SQL: {row[5]}")
    else:
        print("\n✅ No blocking sessions detected")

except cx_Oracle.DatabaseError as e:
    error, = e.args
    print(f"❌ Oracle DB Error: {error.message}")

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()