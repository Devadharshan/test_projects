import subprocess
import re
import logging
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# === CONFIGURATION ===
LOG_DIR = "/path/to/logs"  # 🔧 Update this path
CUSTOM_KEYWORDS = ["CRITICAL", "FATAL"]
ERROR_REGEX = r"\b([A-Z][a-zA-Z0-9]+Error)\b"
EXCEPTION_REGEX = r"\b([A-Z][a-zA-Z0-9]+Exception)\b"
PUSHGATEWAY_URL = "http://your-pushgateway:9091"  # 🔧 Update this URL
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

def safe_metric_name(name: str) -> str:
    """Converts a keyword/type to a safe Prometheus metric name."""
    name = name.lower().replace(" ", "_")
    return re.sub(r'\W|^(?=\d)', '_', name)

def push_metric(keyword_type, keyword_value, count, file_path, line_number):
    filename = file_path.split("/")[-1]
    folder = "/".join(file_path.split("/")[:-1]) or "/"

    registry = CollectorRegistry()

    metric_name = safe_metric_name(f"log_occurrence_{keyword_type}_{keyword_value}")
    description = f"Occurrences of {keyword_type}: {keyword_value}"

    g = Gauge(
        metric_name,
        description,
        labelnames=[
            "app_name", "env", "filename", "folder", "path",
            "date", "line_number"
        ],
        registry=registry
    )

    g.labels(
        app_name=APP_NAME,
        env=ENV,
        filename=filename,
        folder=folder,
        path=file_path,
        date=datetime.now().strftime("%Y-%m-%d"),
        line_number=str(line_number)
    ).set(count)

    try:
        push_to_gateway(
            PUSHGATEWAY_URL,
            job=f"{APP_NAME}_{ENV}_{keyword_type}_{safe_metric_name(keyword_value)}",
            registry=registry
        )
    except Exception as e:
        logging.error(f"❌ Failed to push metric {metric_name}: {e}")

def process_log_file(file_path):
    logging.info(f"📄 Processing file: {file_path}")
    try:
        result = subprocess.run(["cat", file_path], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to read {file_path}: {e}")
        return

    error_map = {}
    exception_map = {}
    custom_map = {}

    for i, line in enumerate(lines, start=1):
        # Errors
        for match in re.findall(ERROR_REGEX, line):
            key = (match, i)
            error_map[key] = error_map.get(key, 0) + 1

        # Exceptions
        for match in re.findall(EXCEPTION_REGEX, line):
            key = (match, i)
            exception_map[key] = exception_map.get(key, 0) + 1

        # Custom keywords
        for keyword in CUSTOM_KEYWORDS:
            if keyword in line:
                key = (keyword, i)
                custom_map[key] = custom_map.get(key, 0) + 1

    for (err, lineno), count in error_map.items():
        push_metric("error", err, count, file_path, lineno)

    for (ex, lineno), count in exception_map.items():
        push_metric("exception", ex, count, file_path, lineno)

    for (kw, lineno), count in custom_map.items():
        push_metric("custom", kw, count, file_path, lineno)

def find_log_files(log_dir):
    try:
        result = subprocess.run(
            ["find", log_dir, "-type", "f"],
            capture_output=True, text=True, check=True
        )
        files = result.stdout.strip().splitlines()
        return [f for f in files if f.endswith((".log", ".out", ".err", ".nohup_log"))]
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to list files in {log_dir}: {e}")
        return []

def main():
    logging.info("🚀 Starting historical log file processing...")
    log_files = find_log_files(LOG_DIR)
    logging.info(f"📁 Found {len(log_files)} log files.")

    for log_file in log_files:
        process_log_file(log_file)

    logging.info("✅ All metrics pushed successfully.")

if __name__ == "__main__":
    main()