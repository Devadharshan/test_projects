import csv
import argparse
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def parse_csv(file_path, gauge_name, registry):
    """
    Parse a CSV file and add metrics to the Prometheus registry with dynamic labels.
    """
    metrics = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        labels = [key for key in reader.fieldnames if key != "value"]  # Extract all columns except "value"

        # Create a Gauge with dynamic labels
        gauge = Gauge(gauge_name, "Description of the gauge", labelnames=labels, registry=registry)

        for row in reader:
            # Extract label values dynamically
            label_values = {label: row[label] for label in labels}
            value = float(row.get("value", 1))  # Default value is 1 if "value" column is missing

            # Set the gauge value for the current labels
            gauge.labels(**label_values).set(value)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Send CSV data to Prometheus Push Gateway.")
    parser.add_argument('--csv', required=True, help="Path to the CSV file.")
    parser.add_argument('--pushgateway', required=True, help="Prometheus Push Gateway URL.")
    parser.add_argument('--gauge_name', required=True, help="Gauge name for the metrics.")
    parser.add_argument('--job_name', required=True, help="Job name for the Push Gateway.")

    args = parser.parse_args()

    # Create a new Prometheus registry
    registry = CollectorRegistry()

    # Parse the CSV and populate the registry
    parse_csv(args.csv, args.gauge_name, registry)

    # Push metrics to the Push Gateway
    push_to_gateway(args.pushgateway, job=args.job_name, registry=registry)
    print(f"Metrics successfully pushed to {args.pushgateway} under job {args.job_name}.")

if __name__ == "__main__":
    main()