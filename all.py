import csv
import sybpydb

def query_sybase_and_save_to_csv(server, user, password, query, output_path):
    try:
        # Connect to Sybase server
        conn = sybpydb.connect(user=user, password=password, servername=server)

        # Execute the query
        cursor = conn.cursor()
        cursor.execute(query)

        # Fetch all results
        results = cursor.fetchall()
        
        # Get column headers
        headers = [desc[0] for desc in cursor.description]

        # Save the result to a CSV file
        with open(output_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            
            # Write headers
            writer.writerow(headers)
            
            # Write data rows
            writer.writerows(results)
        
        print(f"Query results saved to {output_path}")
    
    except sybpydb.DatabaseError as e:
        print(f"Database error occurred: {e}")
    
    finally:
        # Clean up connection
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Example usage
server = "your_server_name"
user = "your_username"
password = "your_password"
query = "SELECT * FROM your_table"
output_path = "/path/to/output_file.csv"

query_sybase_and_save_to_csv(server, user, password, query, output_path)