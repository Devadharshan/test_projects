# Open the text file
with open("your_text_file.txt", "r") as file:
    # Read each line
    for line in file:
        # Split the line based on the "|" delimiter
        servers = line.strip().split(" | ")
        # Iterate over each server in the line
        for server in servers:
            # Split the server name and database name based on "."
            server_name, db_name = server.split(".")
            print("Server:", server_name, "DB:", db_name)





# Open the text file
with open("your_text_file.txt", "r") as file:
    # Read each line
    for line in file:
        # Split the line based on the "|" delimiter
        servers = line.strip().split(" | ")
        # Iterate over each server in the line
        for server in servers:
            # Split the server name and database name based on "."
            try:
                server_name, db_name = server.split(".")
                print("Server:", server_name, "DB:", db_name)
            except ValueError:
                print("Error: Malformed line -", server)




# Open the text file
with open("your_text_file.txt", "r") as file:
    # Read each line
    for line in file:
        # Split the line based on the "|" delimiter
        server_pairs = line.strip().split(" | ")
        # Iterate over each pair of servers
        for server_pair in server_pairs:
            # Split the server name and database name based on "."
            server, db = server_pair.split(".")
            print("Server:", server, "DB:", db)



# Open the text file
with open("your_text_file.txt", "r") as file:
    # Read each line
    for line in file:
        # Split the line based on the "|" delimiter to separate master server from replicas
        master_server, replicas = line.strip().split(" | ")
        
        # Split the master server to get server name and database
        master_server_name, master_db = master_server.split(".")
        print("Master Server:", master_server_name, "DB:", master_db)
        
        # Split the replicas by ","
        replica_servers = replicas.split(",")
        # Iterate over each replica
        for replica_server in replica_servers:
            # Split the replica server to get server name and database
            replica_server_name, replica_db = replica_server.split(".")
            print("Replica Server:", replica_server_name, "DB:", replica_db)