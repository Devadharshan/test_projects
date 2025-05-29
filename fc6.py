from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway
import subprocess
import re
import time
import logging
from pathlib import Path
from collections import defaultdict

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

def aggregate_metrics(filepath: str):
    folder = str(Path(filepath).parent)
    metrics = defaultdict(lambda: {"count": 0, "lines": []})

    try:
        with open(filepath, "r", errors="ignore") as f:
            for line_number, line in enumerate(f, 1):
                # Built-in error/exception
                for label_type, pattern in KEYWORDS.items():
                    match = pattern.search(line)
                    if match:
                        key = (label_type, match.group(), filepath)
                        metrics[key]["count"] += 1
                        if len(metrics[key]["lines"]) < 10:
                            metrics[key]["lines"].append(str(line_number))

                # Custom keywords
                for keyword in CUSTOM_KEYWORDS:
                    if keyword.lower() in line.lower():
                        key = ("custom", keyword, filepath)
                        metrics[key]["count"] += 1
                        if len(metrics[key]["lines"]) < 10:
                            metrics[key]["lines"].append(str(line_number))

    except Exception as e:
        logging.error(f"Could not read {filepath}: {e}")

    return metrics, folder

def push_metrics(aggregated_metrics, folder):
    registry = CollectorRegistry()
    gauge = Gauge(
        "log_occurrence",
        "Log keyword occurrences",
        labelnames=["app", "env", "type", "keyword", "file", "folder", "lines"],
        registry=registry
    )

    for (label_type, keyword, filepath), data in aggregated_metrics.items():
        line_str = ",".join(data["lines"])
        gauge.labels(
            app=APP_NAME,
            env=ENV,
            type=label_type,
            keyword=keyword,
            file=Path(filepath).name,
            folder=folder,
            lines=line_str
        ).set(data["count"])

    try:
        pushadd_to_gateway(PUSHGATEWAY_URL, job=APP_NAME, registry=registry)
        logging.info(f"Pushed {len(aggregated_metrics)} metrics for file: {Path(filepath).name}")
    except Exception as e:
        logging.error(f"Push failed: {e}")

def main():
    log_files = discover_log_files(LOG_DIRECTORY, LOG_EXTENSIONS)
    if not log_files:
        logging.warning("No log files found.")
        return

    for file in log_files:
        aggregated_metrics, folder = aggregate_metrics(file)
        if aggregated_metrics:
            push_metrics(aggregated_metrics, folder)

    logging.info("All done.")

if __name__ == "__main__":
    main()