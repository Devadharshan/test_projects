#!/bin/bash

# ========== CONFIG ==========
PROCESS_USER="process"                        # <--- update if different
WORK_DIR="/path/to/hydra"                     # <--- update folder where hydra_d.py is located
PROCESS_NAME="hydra_d.py"                     # name visible in ps -ef
WEEKEND_PY_SCRIPT="python3 weekend_task.py"   # <--- your weekend python script
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="/var/log/hydra_restart_${TIMESTAMP}.log"
# ============================

WEEKEND_FLAG="$1"
if [[ -z "$WEEKEND_FLAG" ]]; then
    echo "Usage: $0 <yes|no>"
    exit 1
fi

echo "===== Script Started $(date) | Weekend Flag: $WEEKEND_FLAG =====" | tee -a "$LOG_FILE"


# ================= STOP HYDRA =================
sudo su - "$PROCESS_USER" <<EOF
cd "$WORK_DIR"
echo "[INFO] Stopping Hydra..." >> "$LOG_FILE"
python3 hydra_d.py stop procedure >> "$LOG_FILE" 2>&1
python3 hydra_d.py stop node >> "$LOG_FILE" 2>&1
EOF


echo "[INFO] Waiting 120 seconds for hydra to stop..." | tee -a "$LOG_FILE"
sleep 120

# verify stop
if pgrep -fu "$PROCESS_USER" "$PROCESS_NAME" >/dev/null; then
    echo "[ERROR] Hydra still running after stop!" | tee -a "$LOG_FILE"
    exit 1
else
    echo "[INFO] Hydra stopped successfully." | tee -a "$LOG_FILE"
fi


# ================= WEEKEND PYTHON SCRIPT =================
if [[ "$WEEKEND_FLAG" == "yes" ]]; then
    echo "[INFO] Weekend mode: Running python script..." | tee -a "$LOG_FILE"
    
    # run inside process user session
    sudo su - "$PROCESS_USER" <<EOF
cd "$WORK_DIR"
$WEEKEND_PY_SCRIPT >> "$LOG_FILE" 2>&1
exit
EOF

    echo "[INFO] Weekend python script completed." | tee -a "$LOG_FILE"
fi


# ================= START HYDRA =================
sudo su - "$PROCESS_USER" <<EOF
cd "$WORK_DIR"
echo "[INFO] Starting Hydra..." >> "$LOG_FILE"
python3 hydra_d.py start procedure >> "$LOG_FILE" 2>&1
python3 hydra_d.py start node >> "$LOG_FILE" 2>&1
exit
EOF

sleep 15

# verify start
if pgrep -fu "$PROCESS_USER" "$PROCESS_NAME" >/dev/null; then
    echo "[INFO] Hydra started successfully." | tee -a "$LOG_FILE"
else
    echo "[ERROR] Hydra failed to start!" | tee -a "$LOG_FILE"
    exit 1
fi


# ================= HTTPD RESTART =================
echo "[INFO] Restarting HTTPD..." | tee -a "$LOG_FILE"
sudo /usr/sbin/httpd -k restart >> "$LOG_FILE" 2>&1


echo "===== Script Completed $(date) =====" | tee -a "$LOG_FILE"