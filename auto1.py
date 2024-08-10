import subprocess

def check_autosys_job_status(job_name_pattern):
    """
    Check the status of AutoSys jobs that match a specific pattern.

    :param job_name_pattern: The pattern to match job names.
    :return: A dictionary with job names as keys and their statuses as values.
    """
    try:
        # Run the autorep command to get job status for the pattern
        command = f"autorep -J {job_name_pattern}"
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Decode the output to get the job status details
        output = result.stdout.decode('utf-8').strip()
        
        # Process the output and store it in a dictionary
        job_statuses = {}
        for line in output.splitlines():
            if line.startswith(job_name_pattern):
                parts = line.split()
                job_name = parts[0]
                job_status = parts[3]  # Status is usually in the 4th column
                job_statuses[job_name] = job_status

        return job_statuses

    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e.stderr.decode('utf-8')}")
        return None

# Example usage
job_pattern = "JOB_PATTERN*"  # Replace with your job pattern
statuses = check_autosys_job_status(job_pattern)
if statuses:
    for job, status in statuses.items():
        print(f"Job: {job}, Status: {status}")
else:
    print("No jobs found or an error occurred.")
