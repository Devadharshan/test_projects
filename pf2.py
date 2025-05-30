import subprocess
import re
import time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import logging
from pathlib import Path

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Config ---
LOG_PATH = "/path/to/logs"
PUSHGATEWAY_URL = "http://localhost:9091"
JOB_NAME = "log_monitor"
ENV = "prod"
CUSTOM_KEYWORDS = ["timeout", "failed", "refused"]
FILE_EXTENSIONS = [".log", ".err", ".out", ".nohup_log"]

ERROR_PATTERN = re.compile(r"\b\w*Error\w*\b", re.IGNORECASE)
EXCEPTION_PATTERN = re.compile(r"\b\w*Exception\w*\b", re.IGNORECASE)

# --- Collector Registry ---
registry = CollectorRegistry()
log_metric = Gauge('log_occurrence',
                   'Log occurrences with error/exception/custom keyword',
                   ['app_name', 'env', 'file_name', 'folder', 'line_number', 'error_type', 'timestamp'],
                   registry=registry)

# --- Get All Files with Subprocess ---
def get_log_files(path):
    cmd = ["find", path, "-type", "f"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    files = result.stdout.strip().split('\n')
    return [f for f in files if any(f.endswith(ext) for ext in FILE_EXTENSIONS)]

# --- Process File ---
def process_file(file_path):
    app_name = Path(file_path).stem
    folder = str(Path(file_path).parent)
    file_name = Path(file_path).name

    try:
        with open(file_path, 'r', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line_lower = line.lower()

                if any(kw in line_lower for kw in CUSTOM_KEYWORDS) or ERROR_PATTERN.search(line) or EXCEPTION_PATTERN.search(line):
                    match = ERROR_PATTERN.search(line) or EXCEPTION_PATTERN.search(line)
                    error_type = match.group(0) if match else "custom"
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

                    log_metric.labels(
                        app_name=app_name,
                        env=ENV,
                        file_name=file_name,
                        folder=folder,
                        line_number=str(line_num),
                        error_type=error_type,
                        timestamp=timestamp
                    ).set(1)

    except Exception as e:
        logging.error(f"Failed to read {file_path}: {e}")

# --- Main ---
def main():
    logging.info("🔍 Scanning log files...")
    files = get_log_files(LOG_PATH)
    for file in files:
        process_file(file)

    logging.info(" Pushing metrics to PushGateway...")
    try:
        push_to_gateway(PUSHGATEWAY_URL, job=JOB_NAME, registry=registry)
        logging.info("All metrics pushed successfully.")
    except Exception as e:
        logging.error(f" Failed to push metrics: {e}")

if __name__ == "__main__":
    main()

