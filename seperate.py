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