import subprocess
import re
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def get_autosys_job_details(job_name):
    try:
        # Run the Autosys command to get the job details
        result = subprocess.run(['autorep', '-J', job_name], capture_output=True, text=True, check=True)
        
        # Print result for debugging
        print(result.stdout)  # Debugging
        
        # Adjust the regex to capture job details based on the new output format
        job_details_pattern = re.compile(r'^\s*(\S+)\s+(\S+\s+\S+)\s+(\S+\s+\S+)\s+(\S+)', re.MULTILINE)
        match = job_details_pattern.search(result.stdout)
        
        if match:
            job_name = match.group(1)
            start_date = match.group(2)
            end_date = match.group(3)
            status = match.group(4)
        else:
            return "UNKNOWN", None, None

        return status, start_date, end_date
    except subprocess.CalledProcessError as e:
        return "ERROR", None, None

def get_jobs_by_pattern(pattern):
    try:
        # Run the Autosys command to list jobs based on the pattern
        result = subprocess.run(['autorep', '-J', pattern], capture_output=True, text=True, check=True)
        
        # Process the command output to extract job names
        job_names = re.findall(r'^\s*(\S+)', result.stdout, re.MULTILINE)
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
    
    # Define a Gauge for job details
    job_gauge = Gauge('autosys_job_details', 'Autosys job details', ['job_name', 'metric_type'], registry=registry)

    # Add job details to the gauge
    for job_name in job_names:
        status, start_date, end_date = get_autosys_job_details(job_name)
        
        # Convert dates to UNIX timestamps for Prometheus
        start_timestamp = int(datetime.strptime(start_date, '%m/%d/%y %H:%M:%S').timestamp()) if start_date else None
        end_timestamp = int(datetime.strptime(end_date, '%m/%d/%y %H:%M:%S').timestamp()) if end_date else None
        
        # Update Gauge with status, start timestamp, and end timestamp
        if status == 'SU':
            job_gauge.labels(job_name=job_name, metric_type='status').set(1)
        elif status == 'FA':
            job_gauge.labels(job_name=job_name, metric_type='status').set(0)
        elif status == 'OI':
            job_gauge.labels(job_name=job_name, metric_type='status').set(2)
        elif status == 'OH':
            job_gauge.labels(job_name=job_name, metric_type='status').set(3)
        elif status == 'TE':
            job_gauge.labels(job_name=job_name, metric_type='status').set(4)
        else:
            job_gauge.labels(job_name=job_name, metric_type='status').set(-1)  # For unknown or error states

        if start_timestamp:
            job_gauge.labels(job_name=job_name, metric_type='start_timestamp').set(start_timestamp)
        if end_timestamp:
            job_gauge.labels(job_name=job_name, metric_type='end_timestamp').set(end_timestamp)

    # Push all the metrics to the Pushgateway under a single Prometheus job
    push_to_gateway(push_gateway_url, job='autosys_jobs_monitor', registry=registry)
    print("Metrics pushed to Pushgateway.")





import subprocess
import re
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def get_autosys_job_details(job_name):
    try:
        # Run the Autosys command to get the job details
        result = subprocess.run(['autorep', '-J', job_name], capture_output=True, text=True, check=True)
        
        # Print result for debugging
        print(result.stdout)  # Debugging
        
        # Remove separator lines like "-----" or any other similar lines
        filtered_output = "\n".join(line for line in result.stdout.splitlines() if not re.match(r'^[-\s]+$', line))
        
        # Adjust the regex to capture job details based on the new output format
        job_details_pattern = re.compile(r'^\s*(\S+)\s+(\S+\s+\S+)\s+(\S+\s+\S+)\s+(\S+)', re.MULTILINE)
        match = job_details_pattern.search(filtered_output)
        
        if match:
            job_name = match.group(1)
            start_date = match.group(2)
            end_date = match.group(3)
            status = match.group(4)
        else:
            return "UNKNOWN", None, None

        return status, start_date, end_date
    except subprocess.CalledProcessError as e:
        return "ERROR", None, None

def get_jobs_by_pattern(pattern):
    try:
        # Run the Autosys command to list jobs based on the pattern
        result = subprocess.run(['autorep', '-J', pattern], capture_output=True, text=True, check=True)
        
        # Process the command output to extract job names, removing separator lines
        filtered_output = "\n".join(line for line in result.stdout.splitlines() if not re.match(r'^[-\s]+$', line))
        
        # Extract job names from filtered output
        job_names = re.findall(r'^\s*(\S+)', filtered_output, re.MULTILINE)
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
    
    # Define a Gauge for job details
    job_gauge = Gauge('autosys_job_details', 'Autosys job details', ['job_name', 'metric_type'], registry=registry)

    # Add job details to the gauge
    for job_name in job_names:
        status, start_date, end_date = get_autosys_job_details(job_name)
        
        # Convert dates to UNIX timestamps for Prometheus
        start_timestamp = int(datetime.strptime(start_date, '%m/%d/%y %H:%M:%S').timestamp()) if start_date else None
        end_timestamp = int(datetime.strptime(end_date, '%m/%d/%y %H:%M:%S').timestamp()) if end_date else None
        
        # Update Gauge with status, start timestamp, and end timestamp
        if status == 'SU':
            job_gauge.labels(job_name=job_name, metric_type='status').set(1)
        elif status == 'FA':
            job_gauge.labels(job_name=job_name, metric_type='status').set(0)
        elif status == 'OI':
            job_gauge.labels(job_name=job_name, metric_type='status').set(2)
        elif status == 'OH':
            job_gauge.labels(job_name=job_name, metric_type='status').set(3)
        elif status == 'TE':
            job_gauge.labels(job_name=job_name, metric_type='status').set(4)
        else:
            job_gauge.labels(job_name=job_name, metric_type='status').set(-1)  # For unknown or error states

        if start_timestamp:
            job_gauge.labels(job_name=job_name, metric_type='start_timestamp').set(start_timestamp)
        if end_timestamp:
            job_gauge.labels(job_name=job_name, metric_type='end_timestamp').set(end_timestamp)

    # Push all the metrics to the Pushgateway under a single Prometheus job
    push_to_gateway(push_gateway_url, job='autosys_jobs_monitor', registry=registry)
    print("Metrics pushed to Pushgateway.")



job_pattern = 'YOUR_JOB_PATTERN*'
push_gateway_url = 'http://your-pushgateway-url:9091'
main(job_pattern, push_gateway_url)




start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S').timestamp()) if start_date else None
end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S').timestamp()) if end_date else None