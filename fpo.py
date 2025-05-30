from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import subprocess
import hashlib
import os
import re

# --- CONFIGURATION ---
LOG_PATH = "/path/to/your/logs"  # Change this
ENV = "prod"
APP_NAME = "my-app"
PUSHGATEWAY_URL = "http://localhost:9091"
PROCESSED_LOG_FILE = "processed_logs.txt"
LOG_EXTENSIONS = ('.log', '.err', '.out', '.nohup_log')

# --- METRICS SETUP ---
registry = CollectorRegistry()
log_metric = Gauge(
    'log_occurrence',
    'Detected log line occurrence with labels',
    ['app_name', 'env', 'file_name', 'folder', 'line_number', 'error_type', 'error_message'],
    registry=registry
)

# --- REGEX PATTERNS ---
ERROR_PATTERNS = {
    'error': re.compile(r'\b(error)\b', re.IGNORECASE),
    'exception': re.compile(r'\b(exception)\b', re.IGNORECASE),
    'custom': re.compile(r'\b(sql|timeout|connection refused|denied)\b', re.IGNORECASE)
}

# --- Load previously processed entries ---
def load_processed_entries():
    seen = set()
    if os.path.exists(PROCESSED_LOG_FILE):
        with open(PROCESSED_LOG_FILE, 'r') as f:
            for line in f:
                seen.add(line.strip())
    return seen

# --- Save new entry to file ---
def save_processed_entry(entry):
    with open(PROCESSED_LOG_FILE, 'a') as f:
        f.write(entry + '\n')

# --- Process individual log file ---
def process_log_file(filepath, seen_entries):
    try:
        result = subprocess.run(['cat', filepath], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to read: {filepath}")
            return

        lines = result.stdout.splitlines()
        folder, file_name = os.path.split(filepath)

        for i, line in enumerate(lines, start=1):
            for error_type, pattern in ERROR_PATTERNS.items():
                if pattern.search(line):
                    match = pattern.search(line)
                    matched_text = match.group()

                    hash_key = hashlib.md5(f"{filepath}:{i}:{line}".encode()).hexdigest()
                    if hash_key in seen_entries:
                        continue

                    seen_entries.add(hash_key)
                    save_processed_entry(hash_key)

                    log_metric.labels(
                        app_name=APP_NAME,
                        env=ENV,
                        file_name=file_name,
                        folder=folder,
                        line_number=str(i),
                        error_type=error_type,
                        error_message=matched_text
                    ).set(1)
    except Exception as e:
        print(f"Error processing file {filepath}: {e}")

# --- Push metrics to Prometheus PushGateway ---
def push_metrics():
    try:
        push_to_gateway(PUSHGATEWAY_URL, job="log_monitor", registry=registry)
        print("✅ All metrics pushed to PushGateway")
    except Exception as e:
        print(f"❌ Failed to push metrics: {e}")

# --- Main Execution ---
def main():
    seen_entries = load_processed_entries()
    for root, _, files in os.walk(LOG_PATH):
        for file in files:
            if file.endswith(LOG_EXTENSIONS):
                process_log_file(os.path.join(root, file), seen_entries)
    push_metrics()

if __name__ == "__main__":
    main()