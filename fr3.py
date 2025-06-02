import re
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# === CONFIG ===
LOG_DIR = "/path/to/logs"  # ✅ Replace with your actual log directory
APP_NAME = "my_app"
ENV = "prod"
CUSTOM_KEYWORDS = ["timeout", "database", "failure"]
PUSHGATEWAY_URL = "http://localhost:9091"
LOG_MATCH_OUTPUT = "log_matches.txt"
STATE_FILE = "processed_entries.json"

# === LOGGING SETUP ===
logging.basicConfig(
    filename="log_monitor.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === PATTERNS ===
ERROR_PATTERN = re.compile(r'\b\w+Error\b', re.IGNORECASE)
EXCEPTION_PATTERN = re.compile(r'\b\w+Exception\b', re.IGNORECASE)

def load_state():
    if Path(STATE_FILE).exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_line_hash(line):
    return hashlib.md5(line.encode("utf-8")).hexdigest()

def process_log_file(file_path: Path, state: dict):
    error_count = 0
    exception_count = 0
    custom_keyword_count = 0
    match_details = []

    file_id = str(file_path.resolve())
    file_state = state.get(file_id, [])

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f, start=1):
                line_hash = f"{file_path}:{idx}:{get_line_hash(line)}"
                if line_hash in file_state:
                    continue  # Already processed

                matched = False
                if ERROR_PATTERN.search(line):
                    error_count += 1
                    match_details.append(f"{file_path.name}:{idx}: ERROR: {line.strip()}")
                    matched = True
                if EXCEPTION_PATTERN.search(line):
                    exception_count += 1
                    match_details.append(f"{file_path.name}:{idx}: EXCEPTION: {line.strip()}")
                    matched = True
                for keyword in CUSTOM_KEYWORDS:
                    if keyword.lower() in line.lower():
                        custom_keyword_count += 1
                        match_details.append(f"{file_path.name}:{idx}: KEYWORD({keyword}): {line.strip()}")
                        matched = True

                if matched:
                    file_state.append(line_hash)

    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return

    if error_count + exception_count + custom_keyword_count == 0:
        return

    # Save matched lines
    with open(LOG_MATCH_OUTPUT, "a") as f:
        for entry in match_details:
            f.write(entry + "\n")

    # === PUSH METRICS ===
    try:
        registry = CollectorRegistry()
        gauge = Gauge(
            'log_occurrence',
            'Log occurrence counts',
            ['app_name', 'env', 'file_name', 'folder', 'metric_type'],
            registry=registry
        )

        folder = str(file_path.parent)
        file_name = file_path.name

        gauge.labels(APP_NAME, ENV, file_name, folder, "error_count").set(error_count)
        gauge.labels(APP_NAME, ENV, file_name, folder, "exception_count").set(exception_count)
        gauge.labels(APP_NAME, ENV, file_name, folder, "custom_keyword_count").set(custom_keyword_count)

        push_to_gateway(PUSHGATEWAY_URL, job="log_monitor", registry=registry)
        logging.info(f"Pushed metrics for {file_path.name}")

    except Exception as e:
        logging.error(f"Error pushing to Prometheus: {e}")

    # Save updated state
    state[file_id] = file_state

def scan_logs():
    state = load_state()
    extensions = [".log", ".out", ".err", ".nohup_log"]
    all_files = list(Path(LOG_DIR).rglob("*"))
    target_files = [f for f in all_files if f.suffix in extensions and f.is_file()]

    for log_file in target_files:
        process_log_file(log_file, state)

    save_state(state)
    logging.info("✅ All logs processed.")

if __name__ == "__main__":
    scan_logs()
    print("✅ Log monitoring complete.")