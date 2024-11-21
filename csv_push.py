import csv
import requests
import argparse

def parse_csv(file_path, gauge_name):
    """
    Parse a CSV file and prepare Prometheus metrics with the specified gauge name.
    """
    metrics = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            labels = ",".join([f'{key}="{value}"' for key, value in row.items()])
            metric = f'{gauge_name}{{{labels}}} 1'
            metrics.append(metric)
    return metrics

def send_to_pushgateway(metrics, pushgateway_url):
    """
    Send metrics directly to the Prometheus Push Gateway.
    """
    payload = "\n".join(metrics)
    response = requests.put(pushgateway_url, data=payload)
    if response.status_code == 202:
        print("Metrics successfully pushed to the Push Gateway.")
    else:
        print(f"Failed to push metrics: {response.status_code} - {response.text}")

def main():
    parser = argparse.ArgumentParser(description="Send CSV data to Prometheus Push Gateway.")
    parser.add_argument('--csv', required=True, help="Path to the CSV file.")
    parser.add_argument('--pushgateway', required=True, help="Prometheus Push Gateway URL.")
    parser.add_argument('--gauge_name', required=True, help="Gauge name for the metrics.")
    args = parser.parse_args()

    # Parse CSV and send metrics
    metrics = parse_csv(args.csv, args.gauge_name)
    send_to_pushgateway(metrics, args.pushgateway)

if __name__ == "__main__":
    main()



-----


import csv
import requests
import argparse

def parse_csv(file_path, gauge_name):
    """
    Parse a CSV file and prepare Prometheus metrics with the specified gauge name.
    """
    metrics = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Create Prometheus metric format: gauge_name{label1="value1", label2="value2"} 1
            labels = ",".join([f'{key}="{value}"' for key, value in row.items()])
            metric = f'{gauge_name}{{{labels}}} 1'
            metrics.append(metric)
    return metrics

def send_to_pushgateway(metrics, pushgateway_url, job_name):
    """
    Send metrics to the Prometheus Push Gateway under a single job.
    """
    # Combine all metrics into one payload
    payload = "\n".join(metrics) + "\n"
    
    # Send the payload to the specified job in the Push Gateway
    url = f"{pushgateway_url}/metrics/job/{job_name}"
    response = requests.put(url, data=payload)
    
    # Check response status
    if response.status_code == 202:
        print("Metrics successfully pushed to the Push Gateway.")
    else:
        print(f"Failed to push metrics: {response.status_code} - {response.text}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Send CSV data to Prometheus Push Gateway.")
    parser.add_argument('--csv', required=True, help="Path to the CSV file.")
    parser.add_argument('--pushgateway', required=True, help="Prometheus Push Gateway URL.")
    parser.add_argument('--gauge_name', required=True, help="Gauge name for the metrics.")
    parser.add_argument('--job_name', required=True, help="Job name for the Push Gateway.")
    
    args = parser.parse_args()

    # Parse CSV and prepare metrics
    metrics = parse_csv(args.csv, args.gauge_name)
    
    # Send metrics to the Push Gateway under a single job
    send_to_pushgateway(metrics, args.pushgateway, args.job_name)

if __name__ == "__main__":
    main()



-----

How Push Gateway Works
The Prometheus Push Gateway is a component in the Prometheus ecosystem that acts as an intermediary for applications or scripts that cannot be directly scraped by Prometheus. Here's a summary of how it works:

Purpose:
Some applications (e.g., batch jobs, one-off scripts) are short-lived and may not be running when Prometheus scrapes metrics.
The Push Gateway allows these applications to "push" their metrics to a temporary store, which Prometheus can scrape later.
Workflow:
Applications send metrics (via HTTP PUT or POST) to the Push Gateway.
The Push Gateway holds these metrics in memory.
Prometheus scrapes the Push Gateway at regular intervals to retrieve these metrics.
Key Features:
Metrics are organized using job names and optional instance labels.
Data is cleared when no longer needed (you can configure this behavior).
What Is a Gauge?
In Prometheus, a gauge is one of the core metric types.

Definition:
A gauge represents a single numerical value that can go up or down over time.
Examples:
Current temperature: temperature{location="room1"} 23.5
Available memory: memory_available_bytes 2048
Active users: active_users 10
Key Characteristics:
Gauges are ideal for metrics that represent values at a specific point in time.
They differ from counters (another metric type), which can only increase or reset.
What Is a Job?
In Prometheus, a job refers to a logical grouping of metrics collected from a single source or application.

Definition:
A job represents the source of the metrics (e.g., a specific application, script, or batch process).
Purpose:
Jobs help organize metrics from different sources within the same Prometheus system.
Prometheus appends a job label to all metrics scraped or pushed from a specific job.
Example:
Suppose you have two batch jobs:
data_importer
data_cleaner
Each job pushes its metrics separately, and Prometheus assigns a job label to distinguish between the two:
my_metric{job="data_importer",status="success"} 1
my_metric{job="data_cleaner",status="failed"} 1
Difference Between Gauge and Job
Aspect	Gauge	Job
Type	A metric type (one of Prometheus' core data structures).	A label or grouping identifier for metrics.
Purpose	Tracks a numeric value that can go up or down over time.	Identifies the source or context of the metrics.
Scope	Represents individual data points (e.g., memory, CPU).	Groups metrics logically for an application or script.
Examples	cpu_usage, temperature, memory_free.	data_import_job, cleanup_task.
Push Gateway Interaction Between Gauges and Jobs
Gauge:
Represents the data being pushed to the Push Gateway.
Example: temperature{location="room1"} 23.5
Job:
Organizes metrics into logical groups in the Push Gateway.
When pushing metrics, you specify a job name.
Example: Metrics from a temperature-monitoring script might be sent under the job temperature_monitor.
Example Workflow
A script collects temperature data every hour and pushes it to the Push Gateway:
curl -X PUT --data "temperature{location=\"room1\"} 25.5" http://localhost:9091/metrics/job/temperature_monitor
Prometheus scrapes the Push Gateway and organizes the data:
temperature{location="room1",job="temperature_monitor"} 25.5
The temperature metric is a gauge, while temperature_monitor is the job label for these metrics.
Why Use Jobs in Push Gateway?
Jobs let you logically separate metrics from different sources.
They make it easier to filter and query metrics in Prometheus and Grafana.
Example:
You can query all metrics from the data_importer job:
my_metric{job="data_importer"}
