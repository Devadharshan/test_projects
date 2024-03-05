# python sybase row count test

import pypyodbc

# Replace with your Sybase connection details
connection_string = "DRIVER={Adaptive Server Enterprise};SERVER=your_server;PORT=your_port;DATABASE=your_database;UID=your_username;PWD=your_password"

# Connect to the database
conn = pypyodbc.connect(connection_string)

# Create a cursor
cursor = conn.cursor()

# Replace 'your_table' with the name of your table
table_name = 'your_table'

# Execute the SQL query to get row count
cursor.execute(f'SELECT COUNT(*) FROM {table_name}')

# Fetch the result
row_count = cursor.fetchone()[0]

# Print or use the row count as needed
print(f'The row count is: {row_count}')

# Close the connection
conn.close()


# get all the tables in an db 

import pypyodbc

# Replace with your Sybase connection details
connection_string = "DRIVER={Adaptive Server Enterprise};SERVER=your_server;PORT=your_port;DATABASE=your_database;UID=your_username;PWD=your_password"

# Connect to the database
conn = pypyodbc.connect(connection_string)

# Create a cursor
cursor = conn.cursor()

# Get all tables in the database
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_type='BASE TABLE'")

# Fetch all the table names
table_names = [row.table_name for row in cursor.fetchall()]

# Print or use the table names as needed
print("Tables in the database:")
for table_name in table_names:
    print(table_name)

# Close the connection
conn.close()

