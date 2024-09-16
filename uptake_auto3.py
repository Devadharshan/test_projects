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





import subprocess
import re

# Function to get Autosys job statuses using autorep command for multiple job patterns
def get_autosys_status(job_patterns):
    job_statuses = {}
    
    # Define a regex pattern to capture job name and status (4th column in the output)
    status_regex = re.compile(r'(\S+)\s+(\S+\s+\S+)\s+(\S+\s+\S+)\s+(\S+)\s+')

    for pattern in job_patterns:
        # Execute the autorep command to fetch job statuses
        cmd = f"autorep -J {pattern} -s"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = result.stdout.strip()

            # Process the output, split by line, then extract job details using regex
            for line in output.splitlines():
                # Skip header or irrelevant lines
                if line.startswith('Job Name') or line.startswith('---') or not line.strip():
                    continue

                # Use regex to capture the job name and status (4th column)
                match = status_regex.match(line)
                if match:
                    job_name = match.group(1)
                    status = match.group(4)  # 4th capture group is the status (ST column)
                    job_statuses[job_name] = status

        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
    
    return job_statuses

# Example usage
if __name__ == "__main__":
    job_patterns = ['ABC%']  # Pattern to match job names
    job_statuses = get_autosys_status(job_patterns)
    print(job_statuses)  # Output the job statuses as a dictionary






from prometheus_client import CollectorRegistry, Gauge, generate_latest, push_to_gateway
import subprocess

# Function to get Autosys job statuses
def get_autosys_job_status(pattern):
    try:
        # Run the `autorep` command to get job status based on pattern
        result = subprocess.run(['autorep', '-J', pattern, '-s'], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching job status: {e}")
        return None

# Function to parse job status
def parse_job_status(output):
    jobs = []
    lines = output.splitlines()
    for line in lines:
        if line and not line.startswith('---'):
            parts = line.split()
            if len(parts) >= 3:
                job_name = parts[0]
                status = parts[2]  # Adjust based on your output format
                jobs.append((job_name, status))
    return jobs

# Define function to push metrics to Push Gateway
def push_metrics_to_pushgateway(jobs, gateway_url, job_name='autosys_jobs'):
    registry = CollectorRegistry()

    # Define gauges for different statuses
    gauge_success = Gauge('auto_success', 'Jobs that succeeded', ['job_name'], registry=registry)
    gauge_failure = Gauge('auto_failure', 'Jobs that failed', ['job_name'], registry=registry)
    gauge_onice = Gauge('auto_onice', 'Jobs that are on ice', ['job_name'], registry=registry)
    gauge_onhold = Gauge('auto_onhold', 'Jobs that are on hold', ['job_name'], registry=registry)
    gauge_terminated = Gauge('auto_terminated', 'Jobs that are terminated', ['job_name'], registry=registry)

    # Set metric values based on job statuses
    for job_name, status in jobs:
        if status == 'SU':  # Success
            gauge_success.labels(job_name=job_name).set(1)
        elif status == 'FA':  # Failure
            gauge_failure.labels(job_name=job_name).set(1)
        elif status == 'OI':  # On Ice
            gauge_onice.labels(job_name=job_name).set(1)
        elif status == 'OH':  # On Hold
            gauge_onhold.labels(job_name=job_name).set(1)
        elif status == 'TE':  # Terminated
            gauge_terminated.labels(job_name=job_name).set(1)

    # Push to Push Gateway
    push_to_gateway(gateway_url, job=job_name, registry=registry)

# Main execution
if __name__ == '__main__':
    # Define your job pattern and Push Gateway URL
    job_pattern = 'ABC%'  # Replace with your pattern
    pushgateway_url = 'localhost:9091'  # Replace with your Push Gateway URL

    # Fetch job statuses
    output = get_autosys_job_status(job_pattern)
    if output:
        jobs = parse_job_status(output)
        # Push metrics to Push Gateway
        push_metrics_to_pushgateway(jobs, pushgateway_url)
        print("Metrics pushed successfully!")
    else:
        print("Failed to fetch job statuses.")







from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import subprocess

def get_autosys_job_status(pattern):
    try:
        # Run the `autorep` command to get job status based on pattern
        result = subprocess.run(['autorep', '-J', pattern, '-s'], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching job status: {e}")
        return None

def parse_job_status(output):
    jobs = []
    lines = output.splitlines()
    for line in lines:
        if line and not line.startswith('---'):
            parts = line.split()
            if len(parts) >= 3:
                job_name = parts[0]
                status = parts[2]  # Adjust based on your output format
                jobs.append((job_name, status))
    return jobs

def push_metrics_to_pushgateway(jobs, gateway_url, job_name='autosys_jobs'):
    registry = CollectorRegistry()

    # Define gauges for job statuses
    gauge_status = Gauge('auto_status', 'Jobs status', ['status', 'job_name'], registry=registry)

    # Aggregate metrics by status and job name
    for job_name, status in jobs:
        if status == 'SU':  # Success
            gauge_status.labels(status='success', job_name=job_name).set(1)
        elif status == 'FA':  # Failure
            gauge_status.labels(status='failure', job_name=job_name).set(1)
        elif status == 'OI':  # On Ice
            gauge_status.labels(status='onice', job_name=job_name).set(1)
        elif status == 'OH':  # On Hold
            gauge_status.labels(status='onhold', job_name=job_name).set(1)
        elif status == 'TE':  # Terminated
            gauge_status.labels(status='terminated', job_name=job_name).set(1)

    # Push to Push Gateway
    push_to_gateway(gateway_url, job=job_name, registry=registry)

# Main execution
if __name__ == '__main__':
    # Define your job pattern and Push Gateway URL
    job_pattern = 'ABC%'  # Replace with your pattern
    pushgateway_url = 'localhost:9091'  # Replace with your Push Gateway URL

    # Fetch job statuses
    output = get_autosys_job_status(job_pattern)
    if output:
        jobs = parse_job_status(output)
        # Push metrics to Push Gateway
        push_metrics_to_pushgateway(jobs, pushgateway_url)
        print("Metrics pushed successfully!")
    else:
        print("Failed to fetch job statuses.")

