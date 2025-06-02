from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, delete_from_gateway
import hashlib
import os
import re
import subprocess

# --- CONFIGURATION ---
LOG_PATH = "/path/to/your/logs"
ENV = "prod"
APP_NAME = "my-app"
PUSHGATEWAY_URL = "http://localhost:9091"
JOB_NAME = "log_monitor"
PROCESSED_LOG_FILE = "processed_logs.txt"
LOG_EXTENSIONS = ('.log', '.err', '.out', '.nohup_log')

# --- REGEX PATTERNS ---
ERROR_PATTERNS = {
    'error': re.compile(r'\b(error)\b', re.IGNORECASE),
    'exception': re.compile(r'\b(exception)\b', re.IGNORECASE),
    'custom': re.compile(r'\b(sql|timeout|connection refused|denied)\b', re.IGNORECASE)
}

# --- Load processed entries ---
def load_processed_entries():
    seen = set()
    if os.path.exists(PROCESSED_LOG_FILE):
        with open(PROCESSED_LOG_FILE, 'r') as f:
            seen = set(line.strip() for line in f.readlines())
    return seen

# --- Save processed hash entry ---
def save_processed_entry(entry):
    with open(PROCESSED_LOG_FILE, 'a') as f:
        f.write(entry + '\n')

# --- Process logs ---
def process_log_file(filepath, seen_entries, gauge):
    try:
        result = subprocess.run(['cat', filepath], capture_output=True, text=True)
        if result.returncode != 0:
            return
        lines = result.stdout.splitlines()
        folder, file_name = os.path.split(filepath)

        for i, line in enumerate(lines, 1):
            for error_type, pattern in ERROR_PATTERNS.items():
                if pattern.search(line):
                    match_text = pattern.search(line).group()
                    hash_key = hashlib.md5(f"{filepath}:{i}:{line}".encode()).hexdigest()
                    if hash_key in seen_entries:
                        continue
                    seen_entries.add(hash_key)
                    save_processed_entry(hash_key)

                    gauge.labels(
                        app_name=APP_NAME,
                        env=ENV,
                        file_name=file_name,
                        folder=folder,
                        line_number=str(i),
                        error_type=error_type,
                        error_message=match_text
                    ).set(1)
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

# --- Main ---
def main():
    seen = load_processed_entries()
    registry = CollectorRegistry()
    gauge = Gauge(
        'log_occurrence',
        'Detected log line occurrence with labels',
        ['app_name', 'env', 'file_name', 'folder', 'line_number', 'error_type', 'error_message'],
        registry=registry
    )

    # Delete existing job data in PushGateway
    try:
        delete_from_gateway(PUSHGATEWAY_URL, JOB_NAME)
        print(f"✅ Cleared old job data: {JOB_NAME}")
    except Exception as e:
        print(f"⚠️ Could not delete job data: {e}")

    # Process all logs
    for root, _, files in os.walk(LOG_PATH):
        for file in files:
            if file.endswith(LOG_EXTENSIONS):
                process_log_file(os.path.join(root, file), seen, gauge)

    # Push new data
    try:
        push_to_gateway(PUSHGATEWAY_URL, job=JOB_NAME, registry=registry)
        print("✅ Metrics pushed successfully")
    except Exception as e:
        print(f"❌ Push failed: {e}")

if __name__ == "__main__":
    main()