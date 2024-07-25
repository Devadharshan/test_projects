import subprocess
import re

def run_command(command):
    """Runs a command in the shell and returns its output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}")
    return result.stdout

def get_jobs(pattern):
    """Fetches jobs based on the provided pattern."""
    command = f'autorep -J {pattern}'
    output = run_command(command)
    return output

def parse_jobs(output):
    """Parses the jobs output and extracts job names and statuses."""
    job_info = []
    for line in output.splitlines():
        if 'Job Name' in line:
            # Skip header line
            continue
        
        parts = re.split(r'\s+', line.strip())
        if len(parts) >= 3:
            job_name = parts[0]
            job_status = parts[-1]
            job_info.append((job_name, job_status))
    
    return job_info

def main(pattern):
    output = get_jobs(pattern)
    job_info = parse_jobs(output)
    
    for job_name, job_status in job_info:
        print(f"Job Name: {job_name}, Status: {job_status}")

if __name__ == "__main__":
    job_pattern = "*"
    main(job_pattern)
