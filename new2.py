import subprocess
import re

def get_autosys_job_status(job_name):
    try:
        # Run the Autosys command to get the job status
        result = subprocess.run(['autorep', '-J', job_name], capture_output=True, text=True, check=True)

        # Process the command output
        output = result.stdout
        status_match = re.search(r'Status:\s+(\w+)', output)
        if status_match:
            return status_match.group(1)
        else:
            return "Job status not found."
    except subprocess.CalledProcessError as e:
        return f"Error occurred: {e}"

def get_jobs_by_pattern(pattern):
    try:
        # Run the Autosys command to list jobs based on the pattern
        result = subprocess.run(['autorep', '-J', pattern], capture_output=True, text=True, check=True)

        # Process the command output to extract job names
        output = result.stdout
        job_names = re.findall(r'^(\S+)', output, re.MULTILINE)
        return job_names
    except subprocess.CalledProcessError as e:
        return f"Error occurred: {e}"

def main(pattern):
    job_names = get_jobs_by_pattern(pattern)
    if isinstance(job_names, str):
        print(job_names)  # Print error message
        return

    for job_name in job_names:
        status = get_autosys_job_status(job_name)
        print(f"The status of the Autosys job '{job_name}' is: {status}")

# Example usage
job_pattern = 'YOUR_JOB_PATTERN*'
main(job_pattern)




import subprocess
import re

def get_autosys_job_status(job_name):
    try:
        # Run the Autosys command to get the job status
        result = subprocess.run(['autorep', '-J', job_name], capture_output=True, text=True, check=True)
        
        # Print raw output for debugging
        print(f"Raw output for job '{job_name}':")
        print(result.stdout)
        
        # Process the command output
        status_match = re.search(r'Status:\s+(\w+)', result.stdout)
        if status_match:
            return status_match.group(1)
        else:
            return "Job status not found."
    except subprocess.CalledProcessError as e:
        return f"Error occurred: {e}"

def get_jobs_by_pattern(pattern):
    try:
        # Run the Autosys command to list jobs based on the pattern
        result = subprocess.run(['autorep', '-J', pattern], capture_output=True, text=True, check=True)
        
        # Print raw output for debugging
        print(f"Raw output for pattern '{pattern}':")
        print(result.stdout)
        
        # Process the command output to extract job names
        job_names = re.findall(r'^(\S+)', result.stdout, re.MULTILINE)
        return job_names
    except subprocess.CalledProcessError as e:
        return f"Error occurred: {e}"

def main(pattern):
    job_names = get_jobs_by_pattern(pattern)
    if isinstance(job_names, str):
        print(job_names)  # Print error message
        return

    for job_name in job_names:
        status = get_autosys_job_status(job_name)
        print(f"The status of the Autosys job '{job_name}' is: {status}")

# Example usage
job_pattern = 'YOUR_JOB_PATTERN*'
main(job_pattern)