import subprocess
import json
import requests

def get_autosys_status():
    # Run the autorep command to get Autosys job status
    result = subprocess.run(['autorep', '-j', 'ALL'], capture_output=True, text=True)
    output = result.stdout
    return output

def parse_status(output):
    # Parse the command output and convert it to a list of dictionaries
    jobs = []
    lines = output.splitlines()
    for line in lines:
        if line.strip() and not line.startswith("Job Name"):
            parts = line.split()
            job = {
                'Job Name': parts[0],
                'Status': parts[3]  # Adjust based on actual output format
            }
            jobs.append(job)
    return jobs

def convert_json_to_prometheus_metrics(jobs):
    # Convert JSON data to Prometheus metrics format
    metrics = ""
    for job in jobs:
        # Map job status to a numeric value or use a predefined value for simplicity
        status_value = 1 if job["Status"] == 'SU' else 0
        metrics += f'job_status{{job_name="{job["Job Name"]}"}} {status_value}\n'
    return metrics

def push_to_grafana(prometheus_metrics):
    # Push the metrics data to the Prometheus Push Gateway
    response = requests.post('http://your-prometheus-push-gateway:9091/metrics/job/autosys_all_jobs', data=prometheus_metrics)
    return response.status_code

def main():
    output = get_autosys_status()
    jobs = parse_status(output)
    prometheus_metrics = convert_json_to_prometheus_metrics(jobs)
    status_code = push_to_grafana(prometheus_metrics)
    print(f'Status code from Push Gateway: {status_code}')

if __name__ == "__main__":
    main()