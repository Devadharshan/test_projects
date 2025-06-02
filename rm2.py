from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import subprocess
import re
import hashlib
from pathlib import Path
import logging

# ---------------- Configuration ----------------
LOG_DIR = "/path/to/your/logs"  # ✅ Set your log directory here
PUSHGATEWAY_URL = "http://localhost:9091"
JOB_NAME = "log_monitor"
APP_NAME = "my_app"
ENV = "prod"
LOG_EXTENSIONS = (".log", ".err", ".out", ".nohup_log")
CUSTOM_KEYWORDS = ["failure", "timeout", "unavailable"]  # Add custom keywords

# ---------------- Logging Setup ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------- Deduplication Cache ----------------
HASH_CACHE_FILE = "processed_logs.txt"
processed_hashes = set()
if Path(HASH_CACHE_FILE).exists():
    with open(HASH_CACHE_FILE, "r") as f:
        processed_hashes = set(line.strip() for line in f)

# ---------------- Metric Registry ----------------
registry = CollectorRegistry()
gauge = Gauge(
    "log_occurrence",
    "Log error/exception/custom keyword occurrence",
    ["app_name", "env", "file_name", "folder", "line_number", "error_type", "error_message"],
    registry=registry
)

# ---------------- Function to Process a File ----------------
def process_file(file_path):
    logging.info(f"Processing {file_path}")
    try:
        output = subprocess.check_output(['cat', file_path], text=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to read {file_path}: {e}")
        return

    folder = str(Path(file_path).parent)
    file_name = Path(file_path).name

    for i, line in enumerate(output.splitlines(), start=1):
        lower_line = line.lower()

        # Match errors, exceptions or custom keywords
        error_match = re.search(r"(error|exception)", lower_line)
        custom_match = any(kw in lower_line for kw in CUSTOM_KEYWORDS)

        if error_match or custom_match:
            error_type = error_match.group(0) if error_match else "custom"
            error_message = line.strip()

            # Create a hash for deduplication
            line_hash = hashlib.md5(f"{file_name}-{i}-{error_message}".encode()).hexdigest()
            if line_hash in processed_hashes:
                continue

            processed_hashes.add(line_hash)
            with open(HASH_CACHE_FILE, "a") as f:
                f.write(line_hash + "\n")

            gauge.labels(
                app_name=APP_NAME,
                env=ENV,
                file_name=file_name,
                folder=folder,
                line_number=str(i),
                error_type=error_type,
                error_message=error_message[:100]
            ).set(1)

# ---------------- Main Logic ----------------
def main():
    log_files = list(Path(LOG_DIR).rglob("*"))
    for file in log_files:
        if file.is_file() and file.suffix in LOG_EXTENSIONS:
            process_file(str(file))

    try:
        push_to_gateway(
            PUSHGATEWAY_URL,
            job=JOB_NAME,
            registry=registry,
            grouping_key={"instance": "logparser-1"}
        )
        logging.info("✅ All metrics pushed successfully.")
    except Exception as e:
        logging.error(f"❌ Failed to push metrics: {e}")

# ---------------- Run ----------------
if __name__ == "__main__":
    main()