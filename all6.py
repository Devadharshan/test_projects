import subprocess
import re
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def get_autosys_job_details(job_name):
    try:
        # Run the Autosys command to get the job details
        result = subprocess.run(['autorep', '-J', job_name], capture_output=True, text=True, check=True)
        
        # Print the full command output for debugging
        print("Full Output:\n", result.stdout)
        
        # Attempt to remove separator lines and match the actual job details line
        job_details_pattern = re.compile(r'^\s*(\S+)\s+(\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\s+(\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+)\s+(\S+)', re.MULTILINE)
        matches = job_details_pattern.findall(result.stdout)
        
        if matches:
            for match in matches:
                job_name = match[0]
                start_date = match[1]
                end_date = match[2]
                status = match[3]
                run_ntry = match[4]
                pri_xit = match[5]
                
                print(f"Parsed Job Name: {job_name}, Start: {start_date}, End: {end_date}, Status: {status}, Run/Ntry: {run_ntry}, Pri/Xit: {pri_xit}")

                # Convert dates to UNIX timestamps
                try:
                    start_timestamp = int(datetime.strptime(start_date, '%m/%d/%y %H:%M:%S').timestamp()) if start_date else None
                    end_timestamp = int(datetime.strptime(end_date, '%m/%d/%y %H:%M:%S').timestamp()) if end_date else None
                except ValueError as ve:
                    print(f"Error parsing dates for job {job_name}: {ve}")
                    start_timestamp, end_timestamp = None, None

                return status, start_timestamp, end_timestamp, run_ntry, pri_xit
        else:
            print(f"No match found for job: {job_name}")
            return "UNKNOWN", None, None, None, None

    except subprocess.CalledProcessError as e:
        print(f"Error running autorep: {str(e)}")
        return "ERROR", None, None, None, None

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
        print(f"Error running autorep: {str(e)}")
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
        status, start_timestamp, end_timestamp, run_ntry, pri_xit = get_autosys_job_details(job_name)
        
        # Update Gauge with status, start timestamp, end timestamp, run_ntry, and pri_xit
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
        if run_ntry:
            job_gauge.labels(job_name=job_name, metric_type='run_ntry').set(int(run_ntry))
        if pri_xit:
            job_gauge.labels(job_name=job_name, metric_type='pri_xit').set(int(pri_xit))

    # Push all the metrics to the Pushgateway under a single Prometheus job
    push_to_gateway(push_gateway_url, job='autosys_jobs_monitor', registry=registry)
    print("Metrics pushed to Pushgateway.")

if __name__ == "__main__":
    pattern = "YOUR_JOB_PATTERN"  # Replace with your actual job pattern
    push_gateway_url = "http://YOUR_PUSHGATEWAY_URL"  # Replace with your Pushgateway URL
    main(pattern, push_gateway_url)