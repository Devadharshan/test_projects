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



