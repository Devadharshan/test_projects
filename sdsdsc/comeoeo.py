from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import pandas as pd
import glob
import os
from datetime import datetime, timedelta

# ========= CONFIG =========
folder = "./"                             # Folder containing CSV files
pushgateway_url = "http://localhost:9091"
job_name = "csv_data_push"

# ========= HELPERS =========
def extract_date_from_filename(fname):
    # Example file: data_sep252025.csv
    base = os.path.basename(fname).lower()
    for part in base.split("_"):
        try:
            dt = datetime.strptime(part.replace(".csv", ""), "%b%d%Y")
            return dt.strftime("%Y-%m-%d")
        except:
            continue
    return datetime.today().strftime("%Y-%m-%d")

def normalize(df):
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

# ========= DISCOVER FILES =========
main_files = glob.glob(os.path.join(folder, "*main*.csv"))
summary_files = glob.glob(os.path.join(folder, "*summary*.csv"))

registry = CollectorRegistry()

# ========= MAIN METRIC =========
main_metric = Gauge(
    "app_main_row_info",
    "Stores all main data rows",
    labelnames=["file_date"] + ["bp_name","thread_id","job_id","start_time","end_time","duration","no_of_trades","durationpertrade","jobdetails"],
    registry=registry
)

# ========= SUMMARY METRIC =========
summary_metric = Gauge(
    "app_summary_row_info",
    "Stores summary data rows",
    labelnames=["file_date","job_details"],
    registry=registry
)

# ========= PROCESS MAIN FILES =========
for f in main_files:
    df = normalize(pd.read_csv(f))
    file_date = extract_date_from_filename(f)
    for _, r in df.iterrows():
        main_metric.labels(
            file_date=file_date,
            bp_name=str(r.get("bp_name","")),
            thread_id=str(r.get("thread_id","")),
            job_id=str(r.get("job_id","")),
            start_time=str(r.get("start_time","")),
            end_time=str(r.get("end_time","")),
            duration=str(r.get("duration","")),
            no_of_trades=str(r.get("no_of_trades","")),
            durationpertrade=str(r.get("durationpertrade","")),
            jobdetails=str(r.get("jobdetails",""))
        ).set(1)

# ========= PROCESS SUMMARY FILES =========
for f in summary_files:
    df = normalize(pd.read_csv(f))
    file_date = extract_date_from_filename(f)
    for _, r in df.iterrows():
        summary_metric.labels(
            file_date=file_date,
            job_details=str(r.get("job_details",""))
        ).set(1)

# ========= COMPARISON METRICS =========
today = datetime.today().strftime("%Y-%m-%d")
week_ago = (datetime.today()-timedelta(days=7)).strftime("%Y-%m-%d")
month_ago = (datetime.today()-timedelta(days=30)).strftime("%Y-%m-%d")

compare_total = Gauge("app_compare_total_trades", "Trade comparison", ["today","previous"], registry=registry)
compare_avg = Gauge("app_compare_average_duration", "Avg duration comparison", ["today","previous"], registry=registry)
compare_jobs = Gauge("app_compare_jobcount", "Job count comparison", ["today","previous"], registry=registry)

# Today vs Past Week
compare_total.labels(today=today, previous="past_week").set(1)
compare_avg.labels(today=today, previous="past_week").set(1)
compare_jobs.labels(today=today, previous="past_week").set(1)

# Today vs Last Month
compare_total.labels(today=today, previous="last_month").set(1)
compare_avg.labels(today=today, previous="last_month").set(1)
compare_jobs.labels(today=today, previous="last_month").set(1)

# ========= PUSH =========
push_to_gateway(pushgateway_url, job=job_name, registry=registry)

print("✅ ALL DATA + SUMMARY + COMPARISON PUSHED SUCCESSFULLY")