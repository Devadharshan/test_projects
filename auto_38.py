import subprocess
from prometheus_client import CollectorRegistry, Gauge, generate_latest
from prometheus_client.exposition import push_to_gateway

# Define the pattern for the jobs you want to check
job_pattern = 'JOB_PATTERN'  # Replace with your actual job pattern

def get_job_statuses(pattern):
    try:
        # Run autorep command to get job statuses
        result = subprocess.run(['autorep', '-J', pattern], stdout=subprocess.PIPE, text=True, check=True)
        output = result.stdout
        
        # Parse the output - you'll need to customize this based on your actual output format
        lines = output.splitlines()
        job_statuses = {}
        
        for line in lines:
            if not line.strip():
                continue
            # Example line processing - adjust according to your actual line format
            parts = line.split()
            if len(parts) > 1:
                job_name = parts[0]
                status = parts[1]
                job_statuses[job_name] = map_status(status)
        
        return job_statuses
    except subprocess.CalledProcessError as e:
        print(f"Error running autorep command: {e}")
        return {}

def map_status(status_code):
    # Map the status codes to Prometheus-friendly labels
    status_mapping = {
        'OI': 'on_ice',
        'OH': 'on_hold',
        'TE': 'terminated',
        'LR': 'long_running',
        'SU': 'success',
        'FA': 'failure'
    }
    return status_mapping.get(status_code, 'unknown')

def push_metrics_to_gateway(job_statuses):
    registry = CollectorRegistry()
    gauge = Gauge('autosys_job_status', 'Status of Autosys jobs', ['job', 'status'], registry=registry)
    
    for job_name, status in job_statuses.items():
        gauge.labels(job=job_name, status=status).set(1)
    
    # Generate the metrics in Prometheus exposition format
    metrics_data = generate_latest(registry).decode('utf-8')
    
    # Push the metrics to the Push Gateway
    push_to_gateway('push.gateway.url:port', job='my_jobs', registry=registry)  # Replace with your Push Gateway URL

def main():
    job_statuses = get_job_statuses(job_pattern)
    if job_statuses:
        push_metrics_to_gateway(job_statuses)

if __name__ == "__main__":
    main()