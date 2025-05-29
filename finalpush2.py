import subprocess
import re
import logging
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# === CONFIGURATION ===
LOG_DIR = "/path/to/logs"  # <-- Change this to your actual log directory
CUSTOM_KEYWORDS = ["CRITICAL", "FATAL"]
ERROR_REGEX = r"\b([A-Z][a-zA-Z0-9]+Error)\b"
EXCEPTION_REGEX = r"\b([A-Z][a-zA-Z0-9]+Exception)\b"
PUSHGATEWAY_URL = "http://your-pushgateway:9091"
APP_NAME = "my_app"
ENV = "prod"

# === LOGGING SETUP ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log_monitor.log"),
        logging.StreamHandler()
    ]
)

def push_metric(keyword_type, keyword_value, count, file_path, line_content, line_number):
    filename = file_path.split("/")[-1]
    folder = "/".join(file_path.split("/")[:-1]) or "/"

    registry = CollectorRegistry()
    g = Gauge(
        'log_keyword_occurrences',
        'Count of keyword occurrences in logs',
        labelnames=[
            "app_name", "env", "keyword_type", "keyword", "line_content",
            "filename", "folder", "path", "date", "mode", "line_number"
        ],
        registry=registry
    )

    g.labels(
        app_name=APP_NAME,
        env=ENV,
        keyword_type=keyword_type,
        keyword=keyword_value,
        line_content=line_content.strip()[:200],
        filename=filename,
        folder=folder,
        path=file_path,
        date=datetime.now().strftime("%Y-%m-%d"),
        mode="historical",
        line_number=str(line_number)
    ).set(count)

    job_name = f"{APP_NAME}_{ENV}_log_monitor"
    try:
        push_to_gateway(PUSHGATEWAY_URL, job=job_name, registry=registry)
        logging.info(f"Pushed {keyword_type.upper()} '{keyword_value}' at line {line_number} from {file_path}")
    except Exception as e:
        logging.error(f"Failed to push metrics: {e}")

def process_log_file(file_path):
    logging.info(f"Processing file: {file_path}")
    try:
        result = subprocess.run(["cat", file_path], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to read {file_path}: {e}")
        return

    # (keyword, line_content, line_number) -> count
    error_map = {}
    exception_map = {}
    custom_map = {}

    for i, line in enumerate(lines, start=1):
        # Errors
        for match in re.findall(ERROR_REGEX, line):
            key = (match, line.strip(), i)
            error_map[key] = error_map.get(key, 0) + 1

        # Exceptions
        for match in re.findall(EXCEPTION_REGEX, line):
            key = (match, line.strip(), i)
            exception_map[key] = exception_map.get(key, 0) + 1

        # Custom keywords
        for keyword in CUSTOM_KEYWORDS:
            if keyword in line:
                key = (keyword, line.strip(), i)
                custom_map[key] = custom_map.get(key, 0) + 1

    # Push metrics
    for (err, line, lineno), count in error_map.items():
        push_metric("error", err, count, file_path, line, lineno)

    for (ex, line, lineno), count in exception_map.items():
        push_metric("exception", ex, count, file_path, line, lineno)

    for (kw, line, lineno), count in custom_map.items():
        push_metric("custom", kw, count, file_path, line, lineno)

def find_log_files(log_dir):
    try:
        result = subprocess.run(
            ["find", log_dir, "-type", "f"],
            capture_output=True, text=True, check=True
        )
        files = result.stdout.strip().splitlines()
        return [f for f in files if f.endswith((".log", ".out", ".err", ".nohup_log"))]
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to list files in {log_dir}: {e}")
        return []

def main():
    logging.info("Starting historical log file processing...")
    log_files = find_log_files(LOG_DIR)
    logging.info(f"Found {len(log_files)} log files.")

    for log_file in log_files:
        process_log_file(log_file)

    logging.info("Finished processing all log files.")

if __name__ == "__main__":
    main()