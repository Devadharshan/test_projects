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