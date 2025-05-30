import subprocess
import time
import re
import logging
from pathlib import Path
from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway

# ------------------------ CONFIGURATION ------------------------
LOG_DIR = "/path/to/logs"  #  Update this
PUSHGATEWAY_URL = "http://localhost:9091"  # pdate this
APP_NAME = "my_app"
ENV = "prod"
CUSTOM_KEYWORDS = ["timeout", "connection", "unavailable"]

# ------------------------ LOGGING SETUP ------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
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
    metric = Gauge(
        'log_occurrence',
        'Occurrences of errors/exceptions/custom keywords',
        ['app', 'env', 'folder', 'file', 'keyword', 'type', 'line', 'time'],
        registry=registry
    )
    metric.labels(
        app=APP_NAME,
        env=ENV,
        folder=folder,
        file=Path(file_path).name,
        keyword=keyword,
        type=label_type,
        line=str(line_number),
        time=timestamp
    ).set(1)

    pushadd_to_gateway(
        PUSHGATEWAY_URL,
        job=APP_NAME,
        registry=registry,
        grouping_key={
            'file': Path(file_path).name,
            'keyword': keyword,
            'type': label_type,
            'env': ENV
        }
    )

def process_file(file_path):
    folder = str(Path(file_path).parent)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    with open(file_path, 'r', errors='ignore') as f:
        for i, line in enumerate(f, 1):
            matched_keywords = detect_keywords(line, ['error', 'exception'] + CUSTOM_KEYWORDS)
            for keyword in matched_keywords:
                if keyword.lower() in ["error", "exception"]:
                    label_type = "exception" if "exception" in keyword.lower() else "error"
                    # Try to extract type of error/exception
                    match = re.search(r'(\w+Exception|\w+Error)', line)
                    if match:
                        keyword = match.group(1)
                else:
                    label_type = "custom"

                logging.info(f"{file_path} | Line {i} | {label_type.upper()}: {keyword}")
                push_metric(file_path, folder, keyword, label_type, i, timestamp)

def tail_file(file_path):
    folder = str(Path(file_path).parent)
    process = subprocess.Popen(['tail', '-n', '0', '-F', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    line_number = 0
    for line in iter(process.stdout.readline, ''):
        line_number += 1
        matched_keywords = detect_keywords(line, ['error', 'exception'] + CUSTOM_KEYWORDS)
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        for keyword in matched_keywords:
            if keyword.lower() in ["error", "exception"]:
                label_type = "exception" if "exception" in keyword.lower() else "error"
                match = re.search(r'(\w+Exception|\w+Error)', line)
                if match:
                    keyword = match.group(1)
            else:
                label_type = "custom"
            logging.info(f"Tailing {file_path} | Line {line_number} | {label_type.upper()}: {keyword}")
            push_metric(file_path, folder, keyword, label_type, line_number, timestamp)

# ------------------------ MAIN ------------------------
def main():
    log_extensions = [".log", ".err", ".out", ".nohup_log"]
    log_files = []
    # Use subprocess to find files instead of os.walk
    find_cmd = ['find', LOG_DIR, '-type', 'f']
    result = subprocess.run(find_cmd, stdout=subprocess.PIPE, text=True)
    all_files = result.stdout.strip().split('\n')

    for file_path in all_files:
        if any(file_path.endswith(ext) for ext in log_extensions):
            log_files.append(file_path)

    logging.info(f"📂 Found {len(log_files)} log files. Starting historical scan...")

    for file_path in log_files:
        try:
            process_file(file_path)
        except Exception as e:
            logging.error(f"Failed processing {file_path}: {e}")

    logging.info("Historical processing done. Starting live tailing...")

    for file_path in log_files:
        subprocess.Popen(lambda: tail_file(file_path), shell=False)

    logging.info("All done. Tailing in progress...")

if __name__ == "__main__":
    main()
