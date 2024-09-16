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
                # Skip header or irrelevant lines
                if line.startswith('Job Name') or line.startswith('---') or not line.strip():
                    continue

                # Split by spaces or tabs, as columns are space-separated
                columns = line.split()
                
                # Check if we have enough columns (usually >= 6)
                if len(columns) >= 6:
                    job_name = columns[0]  # First column is job name
                    status = columns[3]    # Fourth column is the status
                    job_statuses[job_name] = status  # Add job and status to dictionary

        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
    return job_statuses

# Example usage
if __name__ == "__main__":
    job_patterns = ['ABC%']  # Pattern to match job names
    job_statuses = get_autosys_status(job_patterns)
    print(job_statuses)  # Output the job statuses as a dictionary
