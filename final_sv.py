import csv
import argparse
import re
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def sanitize_label_name(label):
    """
    Sanitize label names by replacing invalid characters with underscores.
    """
    return re.sub(r"[^a-zA-Z0-9_]", "_", label)

def parse_csv(file_path, gauge_name, registry):
    """
    Parse a CSV file and add metrics to the Prometheus registry with sanitized labels.
    """
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        # Sanitize column names to use as label names
        sanitized_labels = [sanitize_label_name(col) for col in reader.fieldnames if col != "value"]

        # Create a Gauge with sanitized labels
        gauge = Gauge(gauge_name, "Description of the gauge", labelnames=sanitized_labels, registry=registry)

        for row in reader:
            # Map sanitized label names to their values
            label_values = {
                sanitize_label_name(label): row[label] for label in reader.fieldnames if label != "value"
            }
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