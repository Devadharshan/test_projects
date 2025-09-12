import oracledb

dsn = "dbserver.company.com:1521/ORCLPDB1"  # adjust
username = "your_user"
password = "your_pass"

with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
    with conn.cursor() as cur:
        
        # 1. Check DB alive
        cur.execute("SELECT 'ALIVE' FROM dual")
        print("DB Status:", cur.fetchone()[0])
        
        # 2. Temp DB space
        print("\nTEMP Tablespace Usage:")
        cur.execute("""
            SELECT tablespace_name,
                   ROUND((SUM(bytes_used)/SUM(bytes_free+bytes_used))*100, 2) AS used_percent
            FROM v$temp_space_header
            GROUP BY tablespace_name
        """)
        for row in cur.fetchall():
            print(f"{row[0]} → {row[1]}% used")
        
        # 3. DB space usage
        print("\nTablespace Usage:")
        cur.execute("""
            SELECT tablespace_name,
                   ROUND((used_space/tablespace_size)*100, 2) AS used_percent
            FROM dba_tablespace_usage_metrics
            ORDER BY used_percent DESC
        """)
        for row in cur.fetchall():
            print(f"{row[0]} → {row[1]}% used")
        
        # 4. Transaction logs
        print("\nRedo Logs:")
        cur.execute("""
            SELECT group#, thread#, sequence#, bytes/1024/1024 AS size_mb, archived, status
            FROM v$log
            ORDER BY group#
        """)
        for row in cur.fetchall():
            print(f"Group {row[0]} | Seq {row[2]} | Size {row[3]} MB | Archived={row[4]} | Status={row[5]}")






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