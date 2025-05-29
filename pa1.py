import re
import subprocess
import sys
from datetime import datetime
from prometheus_client import CollectorRegistry, Counter, push_to_gateway

# === CONFIG ===
LOG_DIR = "/var/log/myapp"  # Change to your logs path
PUSHGATEWAY_URL = "http://your.pushgateway.internal:9091"
APP_NAME = "myapp"
ENV = "prod"
CUSTOM_KEYWORDS = ["timeout", "fatal", "unauthorized"]

# === PATTERNS ===
ERROR_PATTERN = re.compile(r"\b(\w+Error)\b", re.IGNORECASE)
EXCEPTION_PATTERN = re.compile(r"\b(\w+Exception)\b", re.IGNORECASE)
CUSTOM_PATTERN = re.compile("|".join(map(re.escape, CUSTOM_KEYWORDS)), re.IGNORECASE)


def run_cmd(cmd):
    """Run shell command and return output."""
    return subprocess.check_output(cmd, text=True).strip()


def list_log_files(directory):
    """List all *.log files using subprocess."""
    result = subprocess.run(["ls", directory], stdout=subprocess.PIPE, text=True)
    return [
        f"{directory}/{line.strip()}"
        for line in result.stdout.splitlines()
        if line.strip().endswith(".log")
    ]


def get_basename(path):
    return run_cmd(["basename", path])


def get_dirname(path):
    return run_cmd(["dirname", path])


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
        print(f"[ERROR] Failed to push metric: {e}")


def monitor_log_file(file_path):
    print(f"[*] Monitoring {file_path}")
    proc = subprocess.Popen(["tail", "-F", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    line_number = 0
    for line in iter(proc.stdout.readline, ''):
        line_number += 1
        for match in ERROR_PATTERN.findall(line):
            push_metric("error", match, 1, file_path, line_number)
        for match in EXCEPTION_PATTERN.findall(line):
            push_metric("exception", match, 1, file_path, line_number)
        for match in CUSTOM_PATTERN.findall(line):
            push_metric("custom", match.lower(), 1, file_path, line_number)


def spawn_file_monitors():
    """Spawn subprocesses for each log file."""
    files = list_log_files(LOG_DIR)
    for file_path in files:
        subprocess.Popen(["python3", __file__, file_path])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        monitor_log_file(sys.argv[1])
    else:
        spawn_file_monitors()