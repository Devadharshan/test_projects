import re
import time
import subprocess
import threading
from datetime import datetime
from collections import defaultdict, Counter
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# === CONFIGURATION ===
APP_NAME = "my_app"
ENV = "prod"
CUSTOM_KEYWORDS = ["timeout", "connection refused", "failed to connect"]
PUSHGATEWAY_URL = "http://your-push-gateway:9091"  # replace with your PushGateway URL
PUSH_INTERVAL = 10  # seconds

# === PATTERNS ===
ERROR_PATTERN = re.compile(r"\b\w*Error\w*\b", re.IGNORECASE)
EXCEPTION_PATTERN = re.compile(r"\b\w*Exception\w*\b", re.IGNORECASE)
CUSTOM_PATTERN = re.compile("|".join(re.escape(kw) for kw in CUSTOM_KEYWORDS), re.IGNORECASE)

# === Push metrics to Prometheus PushGateway ===
def push_metric(keyword_type, keyword_value, count, file_path, label_type="realtime"):
    registry = CollectorRegistry()
    g = Gauge(
        'log_keyword_occurrences',
        'Count of keyword occurrences in logs',
        labelnames=["app_name", "env", "keyword_type", "keyword", "filename", "folder", "date", "mode"],
        registry=registry
    )

    g.labels(
        app_name=APP_NAME,
        env=ENV,
        keyword_type=keyword_type,
        keyword=keyword_value,
        filename=file_path.split("/")[-1],
        folder="/".join(file_path.split("/")[:-1]),
        date=datetime.now().strftime("%Y-%m-%d"),
        mode=label_type
    ).set(count)

    job_name = f"{APP_NAME}_{ENV}_log_monitor"
    try:
        push_to_gateway(PUSHGATEWAY_URL, job=job_name, registry=registry)
        print(f"[+] Pushed {keyword_type}: {keyword_value}={count} from {file_path}")
    except Exception as e:
        print(f"[ERROR] Failed to push metrics: {e}")

# === Monitor a single log file ===
def monitor_log_file(file_path):
    print(f"[*] Processing historical logs from {file_path}...")

    # HISTORICAL PROCESSING
    hist_counts = {
        "error": Counter(),
        "exception": Counter(),
        "custom": Counter()
    }

    try:
        with open(file_path, "r") as f:
            for line in f:
                for match in ERROR_PATTERN.findall(line):
                    hist_counts["error"][match] += 1
                for match in EXCEPTION_PATTERN.findall(line):
                    hist_counts["exception"][match] += 1
                for match in CUSTOM_PATTERN.findall(line):
                    hist_counts["custom"][match.lower()] += 1
    except Exception as e:
        print(f"[ERROR] Failed to read historical log: {e}")
        return

    # Push all historical counts at once
    for ktype, keywords in hist_counts.items():
        for keyword, count in keywords.items():
            push_metric(ktype, keyword, count, file_path, label_type="historical")

    print(f"[*] Finished historical read, now tailing {file_path} in real-time...")

    # REAL-TIME TAILING
    real_time_counts = {
        "error": Counter(),
        "exception": Counter(),
        "custom": Counter()
    }
    last_push_time = time.time()

    proc = subprocess.Popen(["tail", "-F", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    for line in iter(proc.stdout.readline, ''):
        for match in ERROR_PATTERN.findall(line):
            real_time_counts["error"][match] += 1
        for match in EXCEPTION_PATTERN.findall(line):
            real_time_counts["exception"][match] += 1
        for match in CUSTOM_PATTERN.findall(line):
            real_time_counts["custom"][match.lower()] += 1

        if time.time() - last_push_time >= PUSH_INTERVAL:
            for ktype, keywords in real_time_counts.items():
                for keyword, count in keywords.items():
                    push_metric(ktype, keyword, count, file_path, label_type="realtime")
            real_time_counts = {k: Counter() for k in real_time_counts}
            last_push_time = time.time()

# === List all matching log files using subprocess ===
def list_log_files(directory):
    """Find .log, .out, .err, nohup_log files recursively using 'find'."""
    cmd = ["find", directory, "-type", "f",
           "(", "-name", "*.log", "-o", "-name", "*.out", "-o", "-name", "*.err", "-o", "-name", "*nohup_log", ")"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

# === Start monitoring all files ===
def monitor_directory(directory):
    files = list_log_files(directory)
    print(f"[+] Found {len(files)} log files in {directory}")
    for file_path in files:
        threading.Thread(target=monitor_log_file, args=(file_path,), daemon=True).start()

# === MAIN ===
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python log_monitor.py /path/to/logs/")
        exit(1)

    monitor_directory(sys.argv[1])

    while True:
        time.sleep(10)