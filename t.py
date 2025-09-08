import cx_Oracle

def run_query(host, port, service_name, user, password, query):
    """
    Connects to Oracle DB, executes a query, and returns the results.
    """
    # Create DSN
    dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
    
    # Connect using username/password
    connection = cx_Oracle.connect(user=user, password=password, dsn=dsn)
    
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        connection.close()


# ===== Example usage =====
if __name__ == "__main__":
    host = "your_db_host"
    port = 1521
    service_name = "XEPDB1"
    user = "your_user"
    password = "your_pass"
    
    query = "SELECT sysdate FROM dual"
    results = run_query(host, port, service_name, user, password, query)
    
    for row in results:
        print("Current Date from DB:", row[0])