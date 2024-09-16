import subprocess

# Function to get Autosys job statuses using autorep command for multiple job patterns
def get_autosys_status(job_patterns):
    job_statuses = {}
    for pattern in job_patterns:
        # Execute the autorep command to fetch job statuses
        cmd = f"autorep -J {pattern} -s"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = result.stdout.strip()
            
            # Process the output, split by line, then extract job details
            for line in output.splitlines():
                columns = line.split()
                if len(columns) >= 6:
                    job_name = columns[0]
                    status = columns[3]  # Assuming status is in the 4th column (ST column)
                    job_statuses[job_name] = status
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
    return job_statuses
