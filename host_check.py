import subprocess

# Function to check disk space
def check_disk_space(hostname, threshold):
    print(f"Checking disk space on {hostname}...")
    try:
        df_output = subprocess.check_output(["ssh", hostname, "df -h"], universal_newlines=True)
        disk_lines = df_output.split('\n')[1:]  # Exclude header
        for line in disk_lines:
            device, size, used, available, percent, mountpoint = line.split()
            if percent[:-1] > threshold:
                print(f"Disk space on {hostname} is over {threshold}%.")
                print("Listing files consuming the most space...")
                du_output = subprocess.check_output(["ssh", hostname, "sudo du -ah /"], universal_newlines=True)
                sorted_du = subprocess.check_output(["sort", "-rh"], input=du_output, universal_newlines=True)
                top_files = sorted_du.split('\n')[:10]
                print("\n".join(top_files))
                # Assuming you have a way to push the output to Grafana, do it here
                # For example: requests.post('http://grafana-server/api', data={"message": f"Disk space on {hostname} is over {threshold}%"})
            else:
                print(f"Disk space on {hostname} is below {threshold}%.")
    except Exception as e:
        print(f"Error checking disk space on {hostname}: {e}")

# Set your hosts and threshold here
hosts = ["host1", "host2", "host3"]
threshold = 80

# Loop through each host and check disk space
for host in hosts:
    check_disk_space(host, threshold)