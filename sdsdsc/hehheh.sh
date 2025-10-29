#!/bin/bash

# ========== CONFIG ==========
PROCESS_USER="process"
PROCESS_HOME="/home/process"          # if different, update
WORK_DIR="/path/to/process/dir"       # <-- directory to cd into
PROCESS_NAME="your_process_name"

STOP_COMMAND="./stop.sh"              # example
START_COMMAND="./start.sh"            # example

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="/var/log/process_restart_${TIMESTAMP}.log"
# ============================

WEEKEND_FLAG="$1"
if [[ -z "$WEEKEND_FLAG" ]]; then
    echo "Usage: $0 <yes|no>"
    exit 1
fi

echo "===== Script Started $(date) | Weekend: $WEEKEND_FLAG =====" | tee -a "$LOG_FILE"

# ---------- OPEN A LOGIN SHELL AS process USER ----------
sudo su - "$PROCESS_USER" <<EOF

cd "$WORK_DIR"

echo "[INFO] Stopping process..." >> "$LOG_FILE"
$STOP_COMMAND >> "$LOG_FILE" 2>&1

EOF
# --------------------------------------------------------

echo "[INFO] Waiting for stop (120 seconds)..." | tee -a "$LOG_FILE"
sleep 120

# verify stop
if pgrep -fu "$PROCESS_USER" "$PROCESS_NAME" >/dev/null; then
    echo "[ERROR] Process still running!" | tee -a "$LOG_FILE"
    exit 1
else
    echo "[INFO] Process stopped." | tee -a "$LOG_FILE"
fi


# ---------- WEEKEND EXTRA STEPS ----------
if [[ "$WEEKEND_FLAG" == "yes" ]]; then
echo "[INFO] Weekend patch mode running..." | tee -a "$LOG_FILE"
sudo su - "$PROCESS_USER" <<EOF
cd "$WORK_DIR"
# Add patch commands here:
# example:
# git pull
EOF
fi
# ----------------------------------------


# ---------- START PROCESS ----------
sudo su - "$PROCESS_USER" <<EOF
cd "$WORK_DIR"
echo "[INFO] Starting process..." >> "$LOG_FILE"
$START_COMMAND >> "$LOG_FILE" 2>&1
EOF
# ---------------------------------

sleep 15

if pgrep -fu "$PROCESS_USER" "$PROCESS_NAME" >/dev/null; then
    echo "[INFO] Process started successfully." | tee -a "$LOG_FILE"
else
    echo "[ERROR] Process failed to start." | tee -a "$LOG_FILE"
    exit 1
fi

echo "===== Script Completed $(date) =====" | tee -a "$LOG_FILE"