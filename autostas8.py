import subprocess
import re
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, delete_from_gateway

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
                    if status in ['OI', 'OH']:  # Only capture "On Ice" and "On Hold"
                        job_statuses[job_name] = status

        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
    
    return job_statuses

# Function to push the job statuses to Push Gateway
def push_job_statuses_to_pushgateway(job_statuses, gateway_url):
    registry = CollectorRegistry()

    # Define gauges for on ice and on hold job statuses
    gauge_onice = Gauge('auto_onice', 'On ice jobs', ['job_name'], registry=registry)
    gauge_onhold = Gauge('auto_onhold', 'On hold jobs', ['job_name'], registry=registry)

    # Clear old job metrics before pushing new ones
    delete_from_gateway(gateway_url, job='autosys_jobs')

    # Set metrics for each job based on its status
    for job_name, status in job_statuses.items():
        if status == 'OI':  # On Ice status
            gauge_onice.labels(job_name=job_name).set(1)
        elif status == 'OH':  # On Hold status
            gauge_onhold.labels(job_name=job_name).set(1)

    # Push all metrics to the Push Gateway with the job name in the labels
    push_to_gateway(gateway_url, job='autosys_jobs', registry=registry)

# Example usage
if __name__ == "__main__":
    job_patterns = ['ABC%']  # Pattern to match job names
    job_statuses = get_autosys_status(job_patterns)
    
    if job_statuses:
        pushgateway_url = 'localhost:9091'  # Replace with your Push Gateway URL
        push_job_statuses_to_pushgateway(job_statuses, pushgateway_url)
        print("Job statuses (on ice and on hold) pushed successfully!")
    else:
        print("No job statuses found.")
