import subprocess
from prometheus_client import CollectorRegistry, Gauge, generate_latest, push_to_gateway

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

def collect_metrics(jobs):
    registry = CollectorRegistry()
    # Create a Gauge metric for each job
    for job_name in jobs:
        status = get_autosys_job_status(job_name)
        if status:
            status_pattern = map_status_to_pattern(status)
            metric_name = f'autosys_job_status_{job_name.replace(" ", "_").replace("-", "_")}'
            g = Gauge(metric_name, 'Status of Autosys job', labelnames=['status'], registry=registry)
            g.labels(status=status_pattern).set(1)  # Set to 1 to indicate job is in the given status
    return registry

def push_metrics(pushgateway_url, registry):
    # Push the metrics to Pushgateway
    push_to_gateway(pushgateway_url, job='autosys_jobs', registry=registry)
    print("Metrics pushed to Pushgateway")

# Example usage
job_pattern = 'your_job_pattern*'
pushgateway_url = 'http://localhost:9091'
jobs = get_jobs_by_pattern(job_pattern)

# Collect metrics for all jobs
registry = collect_metrics(jobs)

# Push all collected metrics in one batch
push_metrics(pushgateway_url, registry)