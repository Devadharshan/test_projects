import csv
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# === CONFIGURATION ===
CSV_FILE = "data.csv"                  # path to your CSV file
PUSHGATEWAY_URL = "http://localhost:9091"
JOB_NAME = "csv_metrics"

# === CREATE REGISTRY ===
registry = CollectorRegistry()

# Metric with column and row as labels
metric = Gauge(
    "csv_value",
    "Values from CSV pushed to Prometheus Pushgateway",
    ["column", "row"],
    registry=registry
)

# === READ CSV AND PUSH METRICS ===
with open(CSV_FILE, "r", newline="") as f:
    reader = csv.DictReader(f)
    for row_idx, row in enumerate(reader, start=1):
        for col_name, value in row.items():
            try:
                numeric_value = float(value)
            except ValueError:
                # Skip non-numeric values
                continue
            metric.labels(column=col_name, row=str(row_idx)).set(numeric_value)

# Push to Pushgateway
push_to_gateway(PUSHGATEWAY_URL, job=JOB_NAME, registry=registry)
print(f"✅ Successfully pushed metrics from {CSV_FILE} to {PUSHGATEWAY_URL}")