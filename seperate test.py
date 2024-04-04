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