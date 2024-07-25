import subprocess

def get_autosys_job_status():
    # Command to list all jobs and their statuses
    command = 'autorep -J ALL'

    try:
        # Run the command and capture its output
        output = subprocess.check_output(command, shell=True, universal_newlines=True)
        
        # Split the output by lines
        lines = output.strip().split('\n')
        
        # Initialize a list to store job names and statuses
        jobs = []

        # Process each line (skipping headers if necessary)
        for line in lines:
            # Example format: job_name  status  machine
            parts = line.split()
            if len(parts) >= 2:
                job_name = parts[0]
                status = parts[1]
                jobs.append((job_name, status))
        
        return jobs
    
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(e.output)
        return []

# Example usage
if __name__ == "__main__":
    job_statuses = get_autosys_job_status()
    
    # Print job names and statuses
    for job_name, status in job_statuses:
        print(f"Job: {job_name}, Status: {status}")
