import subprocess
import re
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# === CONFIGURATION ===
LOG_DIR = "/path/to/logs"  # 👈 update this
CUSTOM_KEYWORDS = ["CRITICAL", "FATAL"]
ERROR_REGEX = r"\b(?:[A-Z][a-zA-Z0-9]+Error)\b"
EXCEPTION_REGEX = r"\b(?:[A-Z][a-zA-Z0-9]+Exception)\b"
PUSHGATEWAY_URL = "http://your-pushgateway:9091"
APP_NAME = "my_app"
ENV = "prod"

def push_metric(keyword_type, keyword_value, count, file_path, line_content):
    path = file_path
    filename = file_path.split("/")[-1]
    folder = "/".join(file_path.split("/")[:-1]) or "/"

    registry = CollectorRegistry()
    g = Gauge(
        'log_keyword_occurrences',
        'Count of keyword occurrences in logs',
        labelnames=[
            "app_name", "env", "keyword_type", "keyword", "line_content",
            "filename", "folder", "path", "date", "mode"
        ],
        registry=registry
    )

    g.labels(
        app_name=APP_NAME,
        env=ENV,
        keyword_type=keyword_type,
        keyword=keyword_value,
        line_content=line_content.strip()[:200],  # Avoid long lines
        filename=filename,
        folder=folder,
        path=path,
        date=datetime.now().strftime("%Y-%m-%d"),
        mode="historical"
    ).set(count)

    job_name = f"{APP_NAME}_{ENV}_log_monitor"
    try:
        push_to_gateway(PUSHGATEWAY_URL, job=job_name, registry=registry)
        print(f"[+] Pushed {keyword_type}: {keyword_value} (count={count}) from {path}")
    except Exception as e:
        print(f"[ERROR] Failed to push metrics: {e}")

def process_log_file(file_path):
    print(f"[*] Processing file: {file_path}")
    try:
        result = subprocess.run(["cat", file_path], capture_output=True, text=True)
        lines = result.stdout.splitlines()
    except Exception as e:
        print(f"[ERROR] Cannot read {file_path}: {e}")
        return

    error_map = {}
    exception_map = {}
    custom_map = {}

    for line in lines:
        # Errors
        for error_match in re.findall(ERROR_REGEX, line):
            key = (error_match, line.strip())
            error_map[key] = error_map.get(key, 0) + 1

        # Exceptions
        for ex_match in re.findall(EXCEPTION_REGEX, line):
            key = (ex_match, line.strip())
            exception_map[key] = exception_map.get(key, 0) + 1

        # Custom keywords
        for kw in CUSTOM_KEYWORDS:
            if kw in line:
                key = (kw, line.strip())
                custom_map[key] = custom_map.get(key, 0) + 1

    # Push all metrics
    for (err, line), count in error_map.items():
        push_metric("error", err, count, file_path, line)

    for (ex, line), count in exception_map.items():
        push_metric("exception", ex, count, file_path, line)

    for (kw, line), count in custom_map.items():
        push_metric("custom", kw, count, file_path, line)

def find_log_files(log_dir):
    try:
        result = subprocess.run(["find", log_dir, "-type", "f"], capture_output=True, text=True)
        files = result.stdout.strip().splitlines()
        # Filter desired extensions
        return [f for f in files if f.endswith((".log", ".out", ".err", ".nohup_log"))]
    except Exception as e:
        print(f"[ERROR] Cannot scan directory: {e}")
        return []

def main():
    log_files = find_log_files(LOG_DIR)
    for log_file in log_files:
        process_log_file(log_file)

if __name__ == "__main__":
    main()