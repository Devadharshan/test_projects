import os
import pandas as pd
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from datetime import datetime, timedelta, timezone

# ---------------- CONFIG ----------------
CSV_DIR = r"C:\path\to\csvs"
PUSHGATEWAY_URL = "http://localhost:9091"
JOB_NAME = "bp_aggregated_summary"
IST = timezone(timedelta(hours=5, minutes=30))

WINDOWS = {
    "today": 0,
    "yesterday": 1,
    "last7days": 7,
    "last30days": 30
}

# ---------------- HELPERS ----------------
def parse_date_from_filename(filename):
    try:
        return datetime.strptime(filename.split("__")[-1].split(".csv")[0], "%Y-%m-%d").date()
    except:
        return None

def get_csv_files_for_window(base_dir, window_name):
    today = datetime.now(IST).date()
    files = []
    for f in os.listdir(base_dir):
        if not f.endswith(".csv"):
            continue
        file_date = parse_date_from_filename(f)
        if file_date is None:
            continue
        if window_name == "today" and file_date == today:
            files.append((os.path.join(base_dir, f), file_date))
        elif window_name == "yesterday" and file_date == today - timedelta(days=1):
            files.append((os.path.join(base_dir, f), file_date))
        elif window_name == "last7days" and today - timedelta(days=7) <= file_date <= today - timedelta(days=1):
            files.append((os.path.join(base_dir, f), file_date))
        elif window_name == "last30days" and today - timedelta(days=30) <= file_date <= today - timedelta(days=1):
            files.append((os.path.join(base_dir, f), file_date))
    return sorted(files)

def to_float_safe(val):
    try:
        return float(val)
    except:
        return 0.0

# ---------------- MAIN ----------------
def push_metrics():
    registry = CollectorRegistry()

    # ---------------- GAUGES ----------------
    g_total_trades = Gauge("bp_total_trades", "Total trades per BP", ["bp_name", "job_details", "window", "file_date"], registry=registry)
    g_total_duration = Gauge("bp_total_duration", "Total duration per BP", ["bp_name", "job_details", "window", "file_date"], registry=registry)
    g_avg_duration = Gauge("bp_avg_duration", "Average duration per BP", ["bp_name", "job_details", "window", "file_date"], registry=registry)
    g_avg_duration_per_trade = Gauge("bp_avg_duration_per_trade", "Average duration per trade per BP", ["bp_name", "job_details", "window", "file_date"], registry=registry)
    g_job_count = Gauge("bp_job_count", "Number of jobs per BP", ["bp_name", "job_details", "window", "file_date"], registry=registry)
    g_avg_duration_per_trade_job = Gauge("bp_avg_duration_per_trade_job", "Average duration per trade per BP+JobDetails", ["bp_name", "job_details", "window", "file_date"], registry=registry)
    g_avg_duration_per_bp = Gauge("bp_avg_duration_per_bp", "Average duration per BP", ["bp_name", "job_details", "window", "file_date"], registry=registry)

    # ---------------- PROCESS WINDOWS ----------------
    for window_name in WINDOWS.keys():
        files = get_csv_files_for_window(CSV_DIR, window_name)
        if not files:
            print(f"No CSV files found for window {window_name}")
            continue

        for file_path, file_date in files:
            try:
                df = pd.read_csv(file_path)
                df.columns = [c.strip() for c in df.columns]

                # Ensure required numeric columns exist
                for col in ["Duration", "No of trades", "DurationPerTrade"]:
                    if col not in df.columns:
                        df[col] = 0

                # Fill missing JobDetails column if not present
                if "JobDetails" not in df.columns:
                    df["JobDetails"] = "unknown"

                # Fill NaNs with defaults
                df.fillna("unknown", inplace=True)
                df["Duration"] = df["Duration"].apply(to_float_safe)
                df["No of trades"] = df["No of trades"].apply(to_float_safe)
                df["DurationPerTrade"] = df["DurationPerTrade"].apply(to_float_safe)

                # ---------------- AGGREGATIONS ----------------
                bp_job_group = df.groupby(["BP Name", "JobDetails"]).agg(
                    total_trades=("No of trades", "sum"),
                    total_duration=("Duration", "sum"),
                    avg_duration=("Duration", "mean"),
                    avg_duration_per_trade_job=("DurationPerTrade", "mean"),
                    job_count=("JobDetails", "count"),
                ).reset_index()

                # Average duration per BP (over all jobs)
                bp_avg_group = df.groupby("BP Name").agg(
                    avg_duration_per_bp=("DurationPerTrade", "mean")
                ).reset_index()

                # ---------------- PUSH METRICS ----------------
                for _, row in bp_job_group.iterrows():
                    bp = row["BP Name"]
                    job = row["JobDetails"]
                    fd_str = str(file_date)

                    g_total_trades.labels(bp, job, window_name, fd_str).set(row["total_trades"])
                    g_total_duration.labels(bp, job, window_name, fd_str).set(row["total_duration"])
                    g_avg_duration.labels(bp, job, window_name, fd_str).set(row["avg_duration"])
                    g_avg_duration_per_trade.labels(bp, job, window_name, fd_str).set(row["total_duration"] / max(row["total_trades"], 1))
                    g_job_count.labels(bp, job, window_name, fd_str).set(row["job_count"])
                    g_avg_duration_per_trade_job.labels(bp, job, window_name, fd_str).set(row["avg_duration_per_trade_job"])

                # Push average per BP as a separate gauge
                for _, row in bp_avg_group.iterrows():
                    bp = row["BP Name"]
                    # For simplicity, use "all" as job_details
                    g_avg_duration_per_bp.labels(bp, "all", window_name, fd_str).set(row["avg_duration_per_bp"])

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    # ---------------- PUSH TO PUSHGATEWAY ----------------
    push_to_gateway(PUSHGATEWAY_URL, job=JOB_NAME, registry=registry)
    print("✅ Metrics pushed successfully!")

if __name__ == "__main__":
    push_metrics()