import sybpydb

# Replace these variables with your actual database connection details
server = 'your_server'
database = 'your_database'
username = 'your_username'
password = 'your_password'

# Establish connection
conn = sybpydb.connect(servername=server, dbname=database, user=username, password=password)

# Create a cursor object
cursor = conn.cursor()

# Example: Retrieving tables
cursor.execute("SELECT name FROM sysobjects WHERE type = 'U'")
tables = cursor.fetchall()
table_list = [table[0] for table in tables]
print("Tables:")
print(table_list)

# Example: Retrieving views
cursor.execute("SELECT name FROM sysobjects WHERE type = 'V'")
views = cursor.fetchall()
view_list = [view[0] for view in views]
print("\nViews:")
print(view_list)

# Example: Retrieving procedures
cursor.execute("SELECT name FROM sysobjects WHERE type = 'P'")
procedures = cursor.fetchall()
procedure_list = [procedure[0] for procedure in procedures]
print("\nProcedures:")
print(procedure_list)

# Close cursor and connection
cursor.close()
conn.close()