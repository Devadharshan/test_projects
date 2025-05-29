from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway
import subprocess
import re
import time
import logging
from pathlib import Path

# ---------------- CONFIG ----------------
LOG_DIRECTORY = "/path/to/logs"  # 🔁 Replace with your log directory
PUSHGATEWAY_URL = "http://localhost:9091"  # 🔁 Replace with your Pushgateway URL
APP_NAME = "my_app"
ENV = "prod"
CUSTOM_KEYWORDS = ["timeout", "connection failed", "refused"]
LOG_EXTENSIONS = [".log", ".err", ".out", ".nohup_log"]
# ----------------------------------------

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

# Regex patterns
KEYWORDS = {
    "error": re.compile(r"\b(error|fail|fatal|critical)\b", re.IGNORECASE),
    "exception": re.compile(r"\b(\w*Exception|Throwable|Error:)\b", re.IGNORECASE)
}

def discover_log_files(log_dir: str, extensions: list) -> list:
    files = []
    for ext in extensions:
        result = subprocess.run(
            ["find", log_dir, "-type", "f", "-name", f"*{ext}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        found = result.stdout.strip().split("\n")
        files.extend([f for f in found if f.strip()])
    return files

def push_metric(label_type, keyword, filename, folder_name, line_number):
    # Sanitize metric name
    safe_keyword = re.sub(r'[^a-zA-Z0-9_]', '_', keyword.lower())
    metric_name = f"log_occurrence_{label_type.lower()}_{safe_keyword[:50]}"
    registry = CollectorRegistry()
    gauge = Gauge(
        metric_name,
        f"Occurrences of {label_type}: {keyword}",
        labelnames=["app", "env", "keyword", "file", "folder", "line"],
        registry=registry
    )
    gauge.labels(
        app=APP_NAME,
        env=ENV,
        keyword=keyword,
        file=Path(filename).name,
        folder=folder_name,
        line=str(line_number)
    ).set(1)

    try:
        pushadd_to_gateway(PUSHGATEWAY_URL, job=APP_NAME, registry=registry)
        logging.info(f"Pushed metric: {keyword} in {filename}:{line_number}")
    except Exception as e:
        logging.error(f"Push failed: {e}")

def scan_file_for_keywords(filepath: str):
    folder = str(Path(filepath).parent)
    try:
        with open(filepath, "r", errors="ignore") as f:
            for line_number, line in enumerate(f, 1):
                # Standard error & exception checks
                for label_type, pattern in KEYWORDS.items():
                    match = pattern.search(line)
                    if match:
                        push_metric(label_type, match.group(), filepath, folder, line_number)

                # Custom keyword checks
                for keyword in CUSTOM_KEYWORDS:
                    if keyword.lower() in line.lower():
                        push_metric("custom", keyword, filepath, folder, line_number)
    except Exception as e:
        logging.error(f"Could not read {filepath}: {e}")

def main():
    log_files = discover_log_files(LOG_DIRECTORY, LOG_EXTENSIONS)
    if not log_files:
        logging.warning("No log files found.")
        return

    logging.info(f"Found {len(log_files)} log files.")
    for file in log_files:
        logging.info(f"Scanning: {file}")
        scan_file_for_keywords(file)

    logging.info("All done.")

if __name__ == "__main__":
    main()