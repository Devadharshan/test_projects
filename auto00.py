import subprocess
import re
import argparse
from datetime import datetime, timedelta
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, delete_from_gateway

# Function to load the appropriate autorep module based on the environment
def load_autorep_module(env):
    try:
        if env == 'A':
            subprocess.run(["module", "load", "autorep/A"], check=True)
        elif env == 'B':
            subprocess.run(["module", "load", "autorep/B"], check=True)
        elif env == 'C':
            subprocess.run(["module", "load", "autorep/C"], check=True)
        else:
            raise ValueError("Invalid environment provided. Allowed values are A, B, C.")
        print(f"Loaded autorep module for environment: {env}")
    except subprocess.CalledProcessError as e:
        print(f"Error loading module for env {env}: {e}")
        raise

# Function to calculate the difference between the job date and the current date
def calculate_days_on_status(last_start_time):
    job_time = datetime.strptime(last_start_time, '%m/%d/%y %H:%M:%S')  # Adjust the format based on your output
    current_time = datetime.now()
    return (current_time - job_time).days

# Function to get Autosys job statuses and dates using autorep command for multiple job patterns
def get_autosys_status(job_patterns):
    job_statuses = {}

    # Define a regex pattern to capture job name, status, and start date (4th and 2nd columns in the output)
    status_regex = re.compile(r'(\S+)\s+(\S+\s+\S+)\s+(\S+\s+\S+)\s+(\S+)\s+')

    for pattern in job_patterns:
        # Execute the autorep command to fetch job statuses
        cmd = ["autorep", "-J", pattern, "-s"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout.strip()

            # Process the output, split by line, then extract job details using regex
            for line in output.splitlines():
                # Skip header or irrelevant lines
                if line.startswith('Job Name') or line.startswith('---') or not line.strip():
                    continue

                # Use regex to capture the job name, start time, and status
                match = status_regex.match(line)
                if match:
                    job_name = match.group(1)
                    last_start_time = match.group(2)  # 2nd capture group is the last start time
                    status = match.group(4)  # 4th capture group is the status (ST column)

                    # Only capture jobs On Ice or On Hold, calculate days on status
                    if status in ['OI', 'OH']:
                        days_on_status = calculate_days_on_status(last_start_time)
                        job_statuses[job_name] = (status, days_on_status)

        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
    
    return job_statuses

# Function to push the job statuses to Push Gateway
def push_job_statuses_to_pushgateway(job_statuses, gateway_url):
    registry = CollectorRegistry()

    # Define gauges for on ice and on hold job statuses
    gauge_onice = Gauge('auto_onice', 'On ice jobs', ['job_name', 'days_on_ice'], registry=registry)
    gauge_onhold = Gauge('auto_onhold', 'On hold jobs', ['job_name', 'days_on_hold'], registry=registry)

    # Clear old job metrics before pushing new ones
    delete_from_gateway(gateway_url, job='autosys_jobs')

    # Set metrics for each job based on its status and days on that status
    for job_name, (status, days_on_status) in job_statuses.items():
        if status == 'OI' and days_on_status > 30:  # On Ice status, more than 30 days
            gauge_onice.labels(job_name=job_name, days_on_ice=str(days_on_status)).set(1)
        elif status == 'OH' and days_on_status > 30:  # On Hold status, more than 30 days
            gauge_onhold.labels(job_name=job_name, days_on_hold=str(days_on_status)).set(1)

    # Push all metrics to the Push Gateway with the job name and days in status in the labels
    push_to_gateway(gateway_url, job='autosys_jobs', registry=registry)

# Main function with argument parsing
def main():
    # Argument parser to handle env and push gateway URL
    parser = argparse.ArgumentParser(description="Push Autosys job statuses to Push Gateway")
    parser.add_argument('--env', required=True, help="Environment to load (A, B, or C)")
    parser.add_argument('--gateway-url', required=True, help="Push Gateway URL")

    args = parser.parse_args()

    # Load the appropriate autorep module based on the environment
    load_autorep_module(args.env)

    # Define job patterns directly in the script
    job_patterns = ['ABC%', 'XYZ%']  # Add your job patterns here

    # Get the job statuses
    job_statuses = get_autosys_status(job_patterns)

    # Push job statuses to the Push Gateway
    if job_statuses:
        push_job_statuses_to_pushgateway(job_statuses, args.gateway_url)
        print("Job statuses (on ice and on hold) pushed successfully!")
    else:
        print("No job statuses found.")

if __name__ == "__main__":
    main()
