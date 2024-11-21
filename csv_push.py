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
