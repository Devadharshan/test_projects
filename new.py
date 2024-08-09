import subprocess

def get_autosys_job_status(job_name):
    try:
        # Run the Autosys command to get the job status
        result = subprocess.run(['autorep', '-J', job_name], capture_output=True, text=True, check=True)

        # Process the command output
        output = result.stdout
        if "Status" in output:
            return output.split("Status:")[1].split()[0]
        else:
            return "Job status not found."
    except subprocess.CalledProcessError as e:
        return f"Error occurred: {e}"

# Example usage
job_name = 'YOUR_JOB_NAME'
status = get_autosys_job_status(job_name)
print(f"The status of the Autosys job '{job_name}' is: {status}")