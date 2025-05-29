import re
import subprocess
import time
from datetime import datetime
from prometheus_client import CollectorRegistry, Counter, push_to_gateway

# === CONFIG ===
LOG_DIR = "/var/log/myapp"  # Update with your log directory
PUSHGATEWAY_URL = "http://your.pushgateway.internal:9091"
APP_NAME = "myapp"
ENV = "prod"
CUSTOM_KEYWORDS = ["timeout", "fatal", "unauthorized"]

# === REGEX ===
ERROR_PATTERN = re.compile(r"\b(\w+Error)\b", re.IGNORECASE)
EXCEPTION_PATTERN = re.compile(r"\b(\w+Exception)\b", re.IGNORECASE)
CUSTOM_PATTERN = re.compile("|".join(map(re.escape, CUSTOM_KEYWORDS)), re.IGNORECASE)


def get_basename(path):
    return subprocess.check_output(["basename", path]).decode().strip()


def get_dirname(path):
    return subprocess.check_output(["dirname", path]).decode().strip()


def list_log_files(directory):
    result = subprocess.run(["ls", directory], stdout=subprocess.PIPE, text=True)
    return [
        f"{directory}/{line.strip()}"
        for line in result.stdout.splitlines()
        if line.strip().endswith(".log")
    ]


def push_metric(keyword_type, keyword_value, count, file_path, line_number):
    registry = CollectorRegistry()
    metric = Counter(
        'log_keyword_occurrence_total',
        'Occurrences of keywords in log files',
        [
            'app_name', 'env', 'folder_name', 'file_name', 'date',
            'keyword_type', 'keyword_value', 'line_number'
        ],
        registry=registry
    )

    file_name = get_basename(file_path)
    folder_name = get_basename(get_dirname(file_path))
    date_str = datetime.now().strftime("%Y-%m-%d")

    metric.labels(
        app_name=APP_NAME,
        env=ENV,
        folder_name=folder_name,
        file_name=file_name,
        date=date_str,
        keyword_type=keyword_type,
        keyword_value=keyword_value,
        line_number=str(line_number)
    ).inc(count)

    try:
        push_to_gateway(PUSHGATEWAY_URL, job="log_monitor", registry=registry)
    except Exception as e:
        print(f"[ERROR] Push failed: {e}")


def monitor_log_file(file_path):
    print(f"[*] Monitoring {file_path}")
    process = subprocess.Popen(["tail", "-F", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    line_number = 0
    for line in iter(process.stdout.readline, ''):
        line_number += 1
        for match in ERROR_PATTERN.findall(line):
            push_metric("error", match, 1, file_path, line_number)
        for match in EXCEPTION_PATTERN.findall(line):
            push_metric("exception", match, 1, file_path, line_number)
        for match in CUSTOM_PATTERN.findall(line):
            push_metric("custom", match.lower(), 1, file_path, line_number)


def main():
    log_files = list_log_files(LOG_DIR)
    for file_path in log_files:
        subprocess.Popen(["python3", __file__, file_path])


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        monitor_log_file(sys.argv[1])
    else:
        main()