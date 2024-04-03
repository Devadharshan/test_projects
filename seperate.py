import csv

# Define the filename and separator
filename = 'your_csv_file.csv'
sep = 'sep'  # or whatever separator you're using

# Initialize lists to store data
master_servers = []
master_dbs = []
replica_servers = []
replica_dbs = []

# Read the CSV file and extract data
with open(filename, newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=sep)
    for row in reader:
        master = row['masterserver.dband'].split('.')
        master_servers.append(master[0])
        master_dbs.append(master[1])
        
        replica = row['replicaserver.db'].split('.')
        replica_servers.append(replica[0])
        replica_dbs.append(replica[1])

# Print or manipulate the data as needed
print("Master Servers:", master_servers)
print("Master Databases:", master_dbs)
print("Replica Servers:", replica_servers)
print("Replica Databases:", replica_dbs)





import pandas as pd

# Define the filename and separator
filename = 'your_csv_file.csv'
sep = 'sep'  # or whatever separator you're using

# Read the CSV file into a pandas DataFrame
df = pd.read_csv(filename, sep=sep)

# Split the "masterserver.dband" column into server and database columns
df[['Master Server', 'Master DB']] = df['masterserver.dband'].str.split('.', expand=True)

# Split the "replicaserver.db" column into server and database columns
df[['Replica Server', 'Replica DB']] = df['replicaserver.db'].str.split('.', expand=True)

# Display the DataFrame
print(df)







import csv

# Function to separate server name and database name from a value like "server1.dbname1"
def separate_server_and_db(value):
    server, db = value.split('.')
    return server, db

# Function to read and separate rows and columns of a CSV file
def read_and_separate_servers_dbs(file_path):
    separated_data = []
    with open(file_path, 'r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            separated_columns = []
            for cell in row:
                server, db = separate_server_and_db(cell)
                separated_columns.append((server, db))
            separated_data.append(separated_columns)
    return separated_data

# Input CSV file path
csv_file_path = 'servers.csv'  # Assuming the file is named 'servers.csv'

# Read and separate rows and columns of the CSV file
separated_data = read_and_separate_servers_dbs(csv_file_path)

# Accessing the first row, first column
if len(separated_data) > 0 and len(separated_data[0]) > 0:
    server, db = separated_data[0][0]
    print("First row, first column - Server:", server)
    print("First row, first column - Database:", db)
else:
    print("No data found in the CSV file.")






import csv

# Function to separate server name and database name from a value like "server1.dbname1"
def separate_server_and_db(value):
    if "." in value:
        server, db = value.split('.', 1)  # Limiting split to only split at the first occurrence of "."
        return server, db
    else:
        return None, None  # Return None values if there is no "." in the string

# Function to read and separate rows and columns of a CSV file
def read_and_separate_servers_dbs(file_path):
    separated_data = []
    with open(file_path, 'r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            separated_columns = []
            for cell in row:
                server, db = separate_server_and_db(cell)
                separated_columns.append((server, db))
            separated_data.append(separated_columns)
    return separated_data

# Input CSV file path
csv_file_path = 'servers.csv'  # Assuming the file is named 'servers.csv'

# Read and separate rows and columns of the CSV file
separated_data = read_and_separate_servers_dbs(csv_file_path)

# Accessing the first row, first column
if len(separated_data) > 0 and len(separated_data[0]) > 0:
    server, db = separated_data[0][0]
    print("First row, first column - Server:", server)
    print("First row, first column - Database:", db)
else:
    print("No data found in the CSV file.")




import csv

# Function to read the first row of a CSV file
def read_first_row(file_path):
    with open(file_path, 'r', newline='') as file:
        reader = csv.reader(file)
        first_row = next(reader)  # Read the first row
        return first_row

# Input CSV file path
csv_file_path = 'servers.csv'  # Assuming the file is named 'servers.csv'

# Read the first row of the CSV file
first_row = read_first_row(csv_file_path)

# Print the values from the first row
if len(first_row) >= 2:  # Ensure there are at least two columns in the first row
    server1_dbname1 = first_row[0]  # Value from the first column
    server2_dbname2 = first_row[1]  # Value from the second column
    print("server1.dbname1:", server1_dbname1)
    print("server2.dbname2:", server2_dbname2)
else:
    print("The first row does not contain enough columns.")







# new changes 


import csv

# Function to separate server name and database name from a value like "server1.dbname1"
def separate_server_and_db(value):
    server, db = value.split('.')
    return server, db

# Function to read all rows of a CSV file
def read_all_rows(file_path):
    rows = []
    with open(file_path, 'r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            separated_row = []
            for cell in row:
                server, db = separate_server_and_db(cell)
                separated_row.append((server, db))
            rows.append(separated_row)
    return rows

# Input CSV file path
csv_file_path = 'servers.csv'  # Assuming the file is named 'servers.csv'

# Read all rows of the CSV file and separate server and database names
all_rows = read_all_rows(csv_file_path)

# Print separated server and database names for each row
for row_index, row in enumerate(all_rows):
    print(f"Row {row_index + 1}:")
    for cell_index, (server, db) in enumerate(row):
        print(f"Column {cell_index + 1} - Server: {server}, Database: {db}")

