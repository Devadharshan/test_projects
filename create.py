import subprocess
import requests

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

def format_for_prometheus(job_statuses):
    metrics = []
    for job_name, status in job_statuses.items():
        metric_name = f'autosys_job_status{{job="{job_name}", status="{status}"}}'
        metrics.append(f'{metric_name} 1')
    return '\n'.join(metrics)

def send_to_push_gateway(metrics_data):
    url = 'http://push.gateway.url:port/metrics/job/my_jobs'  # Replace with your Push Gateway URL
    headers = {'Content-Type': 'text/plain'}
    response = requests.post(url, headers=headers, data=metrics_data)
    if response.status_code == 200:
        print("Data successfully sent to Push Gateway")
    else:
        print(f"Failed to send data to Push Gateway: {response.status_code} - {response.text}")

def main():
    job_statuses = get_job_statuses(job_pattern)
    if job_statuses:
        metrics_data = format_for_prometheus(job_statuses)
        send_to_push_gateway(metrics_data)

if __name__ == "__main__":
    main()