import subprocess
import re

def get_job_status(job_names):
    statuses = {}
    for job_name in job_names:
        try:
            # Run the autorep command
            result = subprocess.run(
                ["autorep", "-j", job_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # Parse the result
            output = result.stdout
            # Extract the job status (This is a simplified regex, adjust as needed)
            status_match = re.search(r'Status\s+:\s+(\w+)', output)
            if status_match:
                status = status_match.group(1)
            else:
                status = "Unknown"
            
            statuses[job_name] = status
        
        except subprocess.CalledProcessError as e:
            statuses[job_name] = f"Error: {e.stderr.strip()}"
    
    return statuses

# List of job names you want to check
job_names = ['JOB1', 'JOB2', 'JOB3']

# Get the statuses
status_dict = get_job_status(job_names)

# Print the statuses
for job, status in status_dict.items():
    print(f"{job}: {status}")
