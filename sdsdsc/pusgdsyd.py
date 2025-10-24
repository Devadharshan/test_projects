from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import pandas as pd
import os
from datetime import datetime

# === CONFIG ===
csv_dir = "./csv_files"  # Folder containing all CSVs
pushgateway_url = "http://localhost:9091"  # Change this to your Pushgateway endpoint
job_name = "csv_data_push"

# === INIT PROMETHEUS REGISTRY ===
registry = CollectorRegistry()
gauges = {}

def safe_name(name):
    """Convert column names to Prometheus-safe metric names."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")

# === FUNCTION TO PROCESS EACH CSV ===
def process_csv(file_path, push_time):
    file_name = os.path.basename(file_path)
    print(f"📂 Processing: {file_name}")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Could not read {file_name}: {e}")
        return

    # Clean column names
    safe_col_map = {col: safe_name(col) for col in df.columns}
    df.rename(columns=safe_col_map, inplace=True)

    # Identify numeric and text columns
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    text_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]

    has_job_details = "job_details" in df.columns
    if not numeric_cols:
        print(f"⚠️ No numeric columns found in {file_name}, skipping.")
        return

    # Create Gauges for each numeric column
    for col in numeric_cols:
        metric_name = "csv_" + col
        labelnames = ["file_name", "push_time"]
        if has_job_details:
            labelnames.append("job_details")
        labelnames.append("all_data")

        if metric_name not in gauges:
            gauges[metric_name] = Gauge(
                metric_name,
                f"Metric for column {col}",
                labelnames=labelnames,
                registry=registry
            )

    # Push all rows
    for _, row in df.iterrows():
        all_data = ",".join([f"{k}={v}" for k, v in row.items()])
        for col in numeric_cols:
            try:
                value = float(row[col])
            except Exception:
                continue
            labels = {"file_name": file_name, "push_time": push_time, "all_data": all_data}
            if has_job_details:
                labels["job_details"] = str(row["job_details"])
            gauges["csv_" + col].labels(**labels).set(value)

# === MAIN EXECUTION ===
push_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

for f in os.listdir(csv_dir):
    if f.endswith(".csv"):
        process_csv(os.path.join(csv_dir, f), push_time)

# === PUSH ALL METRICS TO GATEWAY ===
push_to_gateway(pushgateway_url, job=job_name, registry=registry)
print(f"✅ Successfully pushed all CSV metrics to Prometheus Pushgateway at {push_time}!")
