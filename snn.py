import subprocess
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def get_jobs_by_pattern(pattern):
    try:
        result = subprocess.run(
            ['autorep', '-J', pattern],
            capture_output=True,
            text=True,
            check=True
        )
        # Extract job names from the result
        job_lines = result.stdout.splitlines()
        jobs = [line.split()[0] for line in job_lines if line.strip()]
        return jobs
    except subprocess.CalledProcessError as e:
        print(f"Error fetching jobs by pattern: {e}")
        return []

def get_autosys_job_status(job_name):
    try:
        result = subprocess.run(
            ['autorep', '-j', job_name],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse the result to get the status
        status_line = result.stdout.splitlines()[1]
        status = status_line.split()[2]  # Assuming status is in the third column
        return status
    except subprocess.CalledProcessError as e:
        print(f"Error checking job status: {e}")
        return None

def map_status_to_pattern(status):
    status_patterns = {
        'RUNNING': 'running',
        'COMPLETED': 'completed',
        'FAILED': 'failed',
    }
    return status_patterns.get(status.upper(), 'unknown')

def send_status_to_pushgateway(job_name, status_pattern, pushgateway_url):
    registry = CollectorRegistry()
    # Create a valid metric name, replacing invalid characters
    metric_name = f'autosys_job_status_{job_name.replace(" ", "_").replace("-", "_")}'
    
    g = Gauge(metric_name, 'Status of Autosys job', labelnames=['status'], registry=registry)
    g.labels(status=status_pattern).set(1)  # Set to 1 to indicate job is in the given status
    
    push_to_gateway(pushgateway_url, job='autosys_job_status', registry=registry)
    print(f"Sent pattern {status_pattern} for job {job_name} to Pushgateway")

# Example usage
job_pattern = 'your_job_pattern*'
pushgateway_url = 'http://localhost:9091'
jobs = get_jobs_by_pattern(job_pattern)

for job_name in jobs:
    status = get_autosys_job_status(job_name)
    if status:
        status_pattern = map_status_to_pattern(status)
        send_status_to_pushgateway(job_name, status_pattern, pushgateway_url)