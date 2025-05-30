import subprocess
import time
import re
import logging
from pathlib import Path
from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway

# ------------------------ CONFIG ------------------------
LOG_DIR = "/path/to/logs"  # ✅ Set this
PUSHGATEWAY_URL = "http://localhost:9091"  # ✅ Set this
APP_NAME = "log_processor"
ENV = "prod"
CUSTOM_KEYWORDS = ["timeout", "connection", "unavailable"]

# ------------------------ LOGGING ------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ------------------------ FUNCTIONS ------------------------
def detect_keywords(line, keywords):
    matches = []
    for keyword in keywords:
        if keyword.lower() in line.lower():
            matches.append(keyword)
    return matches

def push_metric(file_path, folder, keyword, label_type, line_number, timestamp):
    registry = CollectorRegistry()
    g = Gauge(
        'log_occurrence',
        'Tracks errors, exceptions, and custom keywords in logs',
        ['app', 'env', 'folder', 'file', 'keyword', 'type', 'line_number', 'timestamp'],
        registry=registry
    )

    g.labels(
        app=APP_NAME,
        env=ENV,
        folder=folder,
        file=Path(file_path).name,
        keyword=keyword,
        type=label_type,
        line_number=str(line_number),
        timestamp=timestamp
    ).set(1)

    # ✅ Use unique grouping_key to avoid overwriting
    pushadd_to_gateway(
        PUSHGATEWAY_URL,
        job=APP_NAME,
        registry=registry,
        grouping_key={
            'file': Path(file_path).name,
            'line': str(line_number),
            'keyword': keyword,
            'env': ENV,
        }
    )

def process_file(file_path):
    folder = str(Path(file_path).parent)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(file_path, 'r', errors='ignore') as f:
        for i, line in enumerate(f, 1):
            matches = detect_keywords(line, ['error', 'exception'] + CUSTOM_KEYWORDS)
            for keyword in matches:
                label_type = 'custom'
                if keyword.lower() in ['error', 'exception']:
                    label_type = 'error'
                    match = re.search(r'(\w+Exception|\w+Error)', line)
                    if match:
                        keyword = match.group(1)
                        label_type = 'exception'
                logging.info(f"{file_path} | Line {i} | {label_type.upper()} | {keyword}")
                push_metric(file_path, folder, keyword, label_type, i, timestamp)

# ------------------------ MAIN ------------------------
def main():
    log_extensions = [".log", ".err", ".out", ".nohup_log"]
    log_files = []

    find_cmd = ['find', LOG_DIR, '-type', 'f']
    result = subprocess.run(find_cmd, stdout=subprocess.PIPE, text=True)
    all_files = result.stdout.strip().split('\n')

    for file_path in all_files:
        if any(file_path.endswith(ext) for ext in log_extensions):
            log_files.append(file_path)

    logging.info(f"Found {len(log_files)} files. Processing...")

    for file_path in log_files:
        try:
            process_file(file_path)
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")

    logging.info("✅ All logs processed.")

if __name__ == "__main__":
    main()
