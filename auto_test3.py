from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import subprocess
import json

# Function to get Autosys job statuses using autorep command for multiple job patterns
def get_autosys_status(job_patterns):
    job_statuses = {}
    for pattern in job_patterns:
        # Execute the autorep command to fetch job details
        cmd = f"autorep -J {pattern} -q"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = result.stdout.strip()
            # Process the output, split by line, then extract job details
            for line in output.splitlines():
                columns = line.split()
                if len(columns) >= 6:
                    job_name = columns[0]
                    status = columns[3]  # Assuming status is in the 4th column
                    job_statuses[job_name] = status
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
    return job_statuses

# Function to map status and push to Push Gateway
def push_to_gateway_status(job_statuses, push_gateway_url):
    registry = CollectorRegistry()

    status_labels = {
        'SU': 'auto_success',
        'FA': 'auto_failure',
        'OI': 'auto_onice',
        'OH': 'auto_onhold',
        'TE': 'auto_terminated'
    }

    # Create Gauges for each job status type
    gauges = {
        'auto_success': Gauge('auto_success', 'Number of successful Autosys jobs', registry=registry),
        'auto_failure': Gauge('auto_failure', 'Number of failed Autosys jobs', registry=registry),
        'auto_onice': Gauge('auto_onice', 'Number of on-ice Autosys jobs', registry=registry),
        'auto_onhold': Gauge('auto_onhold', 'Number of on-hold Autosys jobs', registry=registry),
        'auto_terminated': Gauge('auto_terminated', 'Number of terminated Autosys jobs', registry=registry),
    }

    # Initialize job counters
    status_counts = {status: 0 for status in status_labels.values()}

    # Increment counters based on the job statuses
    for job, status in job_statuses.items():
        if status in status_labels:
            status_counts[status_labels[status]] += 1

    # Set the values of the gauges
    for key, count in status_counts.items():
        gauges[key].set(count)

    # Push to Push Gateway
    push_to_gateway(push_gateway_url, job='autosys_status', registry=registry)

# Main script
if __name__ == "__main__":
    job_patterns = ['job_pattern_1', 'job_pattern_2']  # Add job patterns here
    push_gateway_url = "http://your-pushgateway-instance:9091"  # Push Gateway URL

    # Get job statuses from Autosys
    job_statuses = get_autosys_status(job_patterns)

    # Send the job statuses to the Push Gateway
    push_to_gateway_status(job_statuses, push_gateway_url)

    # Optionally, output the job statuses as JSON
    print(json.dumps(job_statuses, indent=4))
