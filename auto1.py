import subprocess

def check_autosys_job_status(job_name_pattern):
    """
    Check the status of AutoSys jobs that match a specific pattern.

    :param job_name_pattern: The pattern to match job names.
    :return: A dictionary with job names as keys and their statuses as values.
    """
    try:
        # Run the autorep command to get job status for the pattern
        command = f"autorep -J {job_name_pattern}"
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Decode the output to get the job status details
        output = result.stdout.decode('utf-8').strip()
        
        # Process the output and store it in a dictionary
        job_statuses = {}
        for line in output.splitlines():
            if line.startswith(job_name_pattern):
                parts = line.split()
                job_name = parts[0]
                job_status = parts[3]  # Status is usually in the 4th column
                job_statuses[job_name] = job_status

        return job_statuses

    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e.stderr.decode('utf-8')}")
        return None

# Example usage
job_pattern = "JOB_PATTERN*"  # Replace with your job pattern
statuses = check_autosys_job_status(job_pattern)
if statuses:
    for job, status in statuses.items():
        print(f"Job: {job}, Status: {status}")
else:
    print("No jobs found or an error occurred.")









import subprocess
import re
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def get_autosys_job_details(job_name):
    try:
        # Run the Autosys command to get the job details
        result = subprocess.run(['autorep', '-J', job_name], capture_output=True, text=True, check=True)
        
        # Process the command output to find status, start date, and end date
        status_match = re.search(r'Status:\s+(\w+)', result.stdout)
        start_date_match = re.search(r'Start Dep:\s+([\d\/:\s]+)', result.stdout)
        end_date_match = re.search(r'End Dep:\s+([\d\/:\s]+)', result.stdout)
        
        status = status_match.group(1) if status_match else "UNKNOWN"
        start_date = start_date_match.group(1).strip() if start_date_match else None
        end_date = end_date_match.group(1).strip() if end_date_match else None
        
        return status, start_date, end_date
    except subprocess.CalledProcessError as e:
        return "ERROR", None, None

def get_jobs_by_pattern(pattern):
    try:
        # Run the Autosys command to list jobs based on the pattern
        result = subprocess.run(['autorep', '-J', pattern], capture_output=True, text=True, check=True)
        
        # Process the command output to extract job names
        job_names = re.findall(r'^(\S+)', result.stdout, re.MULTILINE)
        return job_names
    except subprocess.CalledProcessError as e:
        return []

def main(pattern, push_gateway_url):
    job_names = get_jobs_by_pattern(pattern)
    if not job_names:
        print("No jobs found or error occurred.")
        return

    # Create a registry
    registry = CollectorRegistry()
    
    # Define Gauges for status, start date, and end date
    status_gauge = Gauge('autosys_job_status', 'Autosys job status', ['job_name'], registry=registry)
    start_date_gauge = Gauge('autosys_job_start_timestamp', 'Autosys job start date as timestamp', ['job_name'], registry=registry)
    end_date_gauge = Gauge('autosys_job_end_timestamp', 'Autosys job end date as timestamp', ['job_name'], registry=registry)

    # Add job details to the gauges
    for job_name in job_names:
        status, start_date, end_date = get_autosys_job_details(job_name)
        
        # Convert dates to UNIX timestamps for Prometheus
        start_timestamp = int(datetime.strptime(start_date, '%m/%d/%y %H:%M:%S').timestamp()) if start_date else None
        end_timestamp = int(datetime.strptime(end_date, '%m/%d/%y %H:%M:%S').timestamp()) if end_date else None
        
        # Update Gauges based on job status
        if status == 'SUCCESS':
            status_gauge.labels(job_name=job_name).set(1)
        elif status == 'FAILURE':
            status_gauge.labels(job_name=job_name).set(0)
        elif status == 'ON_ICE':
            status_gauge.labels(job_name=job_name).set(2)
        elif status == 'ON_HOLD':
            status_gauge.labels(job_name=job_name).set(3)
        elif status == 'TERMINATED':
            status_gauge.labels(job_name=job_name).set(4)
        else:
            status_gauge.labels(job_name=job_name).set(-1)  # For unknown or error states
        
        if start_timestamp:
            start_date_gauge.labels(job_name=job_name).set(start_timestamp)
        if end_timestamp:
            end_date_gauge.labels(job_name=job_name).set(end_timestamp)

    # Push all the metrics to the Pushgateway under a single Prometheus job
    push_to_gateway(push_gateway_url, job='autosys_jobs_monitor', registry=registry)
    print("Metrics pushed to Pushgateway.")

# Example usage
job_pattern = 'YOUR_JOB_PATTERN*'
push_gateway_url = 'http://your-pushgateway-url:9091'
main(job_pattern, push_gateway_url)





import subprocess
import re
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def get_autosys_job_details(job_name):
    try:
        # Run the Autosys command to get the job details
        result = subprocess.run(['autorep', '-J', job_name], capture_output=True, text=True, check=True)
        
        # Print result for debugging
        print(result.stdout)  # This will help you see what the script is processing
        
        # Adjust the regex based on the actual output
        status_match = re.search(r'Status:\s+(\w+)', result.stdout)
        start_date_match = re.search(r'Start Dep:\s+([\d\/:\s]+)', result.stdout)
        end_date_match = re.search(r'End Dep:\s+([\d\/:\s]+)', result.stdout)
        
        status = status_match.group(1) if status_match else "UNKNOWN"
        start_date = start_date_match.group(1).strip() if start_date_match else None
        end_date = end_date_match.group(1).strip() if end_date_match else None
        
        return status, start_date, end_date
    except subprocess.CalledProcessError as e:
        return "ERROR", None, None

def get_jobs_by_pattern(pattern):
    try:
        # Run the Autosys command to list jobs based on the pattern
        result = subprocess.run(['autorep', '-J', pattern], capture_output=True, text=True, check=True)
        
        # Process the command output to extract job names
        job_names = re.findall(r'^(\S+)', result.stdout, re.MULTILINE)
        return job_names
    except subprocess.CalledProcessError as e:
        return []

def main(pattern, push_gateway_url):
    job_names = get_jobs_by_pattern(pattern)
    if not job_names:
        print("No jobs found or error occurred.")
        return

    # Create a registry
    registry = CollectorRegistry()
    
    # Define Gauges for status, start date, and end date
    status_gauge = Gauge('autosys_job_status', 'Autosys job status', ['job_name'], registry=registry)
    start_date_gauge = Gauge('autosys_job_start_timestamp', 'Autosys job start date as timestamp', ['job_name'], registry=registry)
    end_date_gauge = Gauge('autosys_job_end_timestamp', 'Autosys job end date as timestamp', ['job_name'], registry=registry)

    # Add job details to the gauges
    for job_name in job_names:
        status, start_date, end_date = get_autosys_job_details(job_name)
        
        # Convert dates to UNIX timestamps for Prometheus
        start_timestamp = int(datetime.strptime(start_date, '%m/%d/%y %H:%M:%S').timestamp()) if start_date else None
        end_timestamp = int(datetime.strptime(end_date, '%m/%d/%y %H:%M:%S').timestamp()) if end_date else None
        
        # Update Gauges based on job status
        if status == 'SUCCESS':
            status_gauge.labels(job_name=job_name).set(1)
        elif status == 'FAILURE':
            status_gauge.labels(job_name=job_name).set(0)
        elif status == 'ON_ICE':
            status_gauge.labels(job_name=job_name).set(2)
        elif status == 'ON_HOLD':
            status_gauge.labels(job_name=job_name).set(3)
        elif status == 'TERMINATED':
            status_gauge.labels(job_name=job_name).set(4)
        else:
            status_gauge.labels(job_name=job_name).set(-1)  # For unknown or error states
        
        if start_timestamp:
            start_date_gauge.labels(job_name=job_name).set(start_timestamp)
        if end_timestamp:
            end_date_gauge.labels(job_name=job_name).set(end_timestamp)

    # Push all the metrics to the Pushgateway under a single Prometheus job
    push_to_gateway(push_gateway_url, job='autosys_jobs_monitor', registry=registry)
    print("Metrics pushed to Pushgateway.")

# Example usage
job_pattern = 'YOUR_JOB_PATTERN*'
push_gateway_url = 'http://your-pushgateway-url:9091'
main(job_pattern, push_gateway_url)

