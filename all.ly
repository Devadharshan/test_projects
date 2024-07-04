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

try:
    # Query for CPU and memory usage
    cursor.execute("""
        SELECT 
            spid,
            cmd,
            cpu,
            physical_io,
            memusage
        FROM master..sysprocesses
        WHERE status = 'runnable' OR status = 'suspended'
    """)
    cpu_memory_usage = cursor.fetchall()

    # Query for blocking processes
    cursor.execute("""
        SELECT 
            spid,
            blocked,
            waittime,
            lastwaittype,
            loginame,
            hostname,
            cmd
        FROM master..sysprocesses
        WHERE blocked != 0
    """)
    blocking_processes = cursor.fetchall()

    # Query for data and log segment information
    cursor.execute("""
        SELECT 
            dbid,
            segmap,
            lstart,
            unreservedpgs,
            vstart
        FROM master..sysusages
    """)
    segments_info = cursor.fetchall()

    # Display results
    print("CPU and Memory Usage:")
    for process in cpu_memory_usage:
        print(process)

    print("\nBlocking Processes:")
    for process in blocking_processes:
        print(process)

    print("\nSegment Information:")
    for segment in segments_info:
        print(segment)

except sybpydb.Error as e:
    print(f"Error: {e}")

finally:
    # Close cursor and connection
    cursor.close()
    conn.close()









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

try:
    # Query for CPU and memory usage
    cursor.execute("""
        SELECT 
            spid,
            cmd,
            cpu,
            physical_io,
            memusage
        FROM master..sysprocesses
        WHERE status = 'runnable' OR status = 'suspended'
    """)
    processes = cursor.fetchall()

    total_cpu_time = sum(process['cpu'] for process in processes)
    total_mem_usage_kb = sum(process['memusage'] for process in processes)

    # Calculate CPU usage percentage
    cpu_usage_percentages = [(process['cpu'] / total_cpu_time) * 100 if total_cpu_time > 0 else 0 for process in processes]

    # Calculate Memory usage percentage
    total_mem_usage_mb = total_mem_usage_kb / 1024  # Convert total memory usage to MB
    mem_usage_percentages = [(process['memusage'] / total_mem_usage_kb) * 100 if total_mem_usage_kb > 0 else 0 for process in processes]

    # Display results
    print("CPU and Memory Usage Percentages:")
    for i, process in enumerate(processes):
        print(f"Process {i + 1}:")
        print(f"    CPU Usage: {cpu_usage_percentages[i]:.2f}%")
        print(f"    Memory Usage: {mem_usage_percentages[i]:.2f}%")

except sybpydb.Error as e:
    print(f"Error: {e}")

finally:
    # Close cursor and connection
    cursor.close()
    conn.close()






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

try:
    # Query for CPU and memory usage
    cursor.execute("""
        SELECT 
            spid,
            cmd,
            cpu,
            physical_io,
            memusage
        FROM master..sysprocesses
        WHERE status = 'runnable' OR status = 'suspended'
    """)
    processes = cursor.fetchall()

    total_cpu_time = sum(process['cpu'] for process in processes)
    total_mem_usage_kb = sum(process['memusage'] for process in processes)

    # Calculate CPU usage percentage
    cpu_usage_percentages = [(process['cpu'] / total_cpu_time) * 100 if total_cpu_time > 0 else 0 for process in processes]

    # Calculate Memory usage percentage
    total_mem_usage_mb = total_mem_usage_kb / 1024  # Convert total memory usage to MB
    mem_usage_percentages = [(process['memusage'] / total_mem_usage_kb) * 100 if total_mem_usage_kb > 0 else 0 for process in processes]

    # Display results
    print("CPU and Memory Usage Percentages:")
    for i, process in enumerate(processes):
        print(f"Process {i + 1}:")
        print(f"    CPU Usage: {cpu_usage_percentages[i]:.2f}%")
        print(f"    Memory Usage: {mem_usage_percentages[i]:.2f}%")

except sybpydb.Error as e:
    print(f"Error: {e}")

finally:
    # Close cursor and connection
    cursor.close()
    conn.close()