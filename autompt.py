import subprocess
from prometheus_client import CollectorRegistry, Gauge, generate_latest, push_to_gateway

def get_autosys_job_status(job_name):
    try:
        result = subprocess.run(
            ['autorep', '-j', job_name],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse the result to get the status
        # Assuming that the job status is in the second line
        status_line = result.stdout.splitlines()[1]
        status = status_line.split()[2]  # Assuming status is in the third column
        return status
    except subprocess.CalledProcessError as e:
        print(f"Error checking job status: {e}")
        return None

def map_status_to_pattern(status):
    # Map job status to a pattern
    status_patterns = {
        'RUNNING': 'AbcRunning%',
        'COMPLETED': 'AbcCompleted%',
        'FAILED': 'AbcFailed%',
    }
    return status_patterns.get(status.upper(), 'AbcUnknown%')  # Default to 'AbcUnknown%' if status is unknown

def send_status_to_pushgateway(job_name, status_pattern, pushgateway_url):
    registry = CollectorRegistry()
    g = Gauge(f'autosys_job_status_{job_name}', 'Status of Autosys job', registry=registry)
    
    # Set the value to 1 or another indicative number to signify the presence of the status
    g.set(1)
    
    # Push the metric with the pattern as an additional label
    push_to_gateway(pushgateway_url, job='autosys_job_status', job_name=job_name, registry=registry)
    
    # For demonstration, print the pattern
    print(f"Sending pattern {status_pattern} for job {job_name} to Pushgateway")

# Example usage
job_name = 'your_job_name'
status = get_autosys_job_status(job_name)
if status:
    status_pattern = map_status_to_pattern(status)
    pushgateway_url = 'http://localhost:9091'
    send_status_to_pushgateway(job_name, status_pattern, pushgateway_url)