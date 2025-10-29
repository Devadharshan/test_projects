#!/bin/bash

PROCESS_USER="process"
WORK_DIR="/app/software/bin"
LOG_FILE="restart_$(date +%Y-%m-%d_%H-%M-%S).log"

WEEKEND_FLAG="$1"   # yes or no (pass this when running script)

echo "========== Restart Script Started ==========" | tee -a "$LOG_FILE"
echo "Weekend Flag: $WEEKEND_FLAG" | tee -a "$LOG_FILE"
echo "Log File: $LOG_FILE" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"

# Switch into application user and run commands
sudo su - "$PROCESS_USER" <<EOF >> "$LOG_FILE" 2>&1
cd "$WORK_DIR"

### --- Normal restart executed ALWAYS --- ###
echo "[NORMAL RESTART] Stopping main process..."
./process stop

echo "Waiting for stop..."
sleep 120
ps -ef | grep process | grep -v grep || echo "Process stopped successfully."

echo "[NORMAL RESTART] Starting main process..."
./process start

echo "Waiting for start..."
sleep 120
ps -ef | grep process | grep -v grep && echo "Process started successfully."


### --- Weekend extra steps executed only if flag is yes --- ###
if [ "$WEEKEND_FLAG" == "yes" ]; then
    echo "[WEEKEND EXTRA] Stopping hydra..."
    ./hydra_d.py stop node

    echo "Waiting for hydra stop..."
    sleep 120
    ps -ef | grep hydra_d | grep -v grep || echo "Hydra stopped successfully."

    echo "[WEEKEND EXTRA] Starting hydra..."
    ./hydra_d.py start node

    echo "Waiting for hydra start..."
    sleep 120
    ps -ef | grep hydra_d | grep -v grep && echo "Hydra started successfully."
fi

exit
EOF

# After leaving su user, restart httpd only if weekend flag yes
if [ "$WEEKEND_FLAG" == "yes" ]; then
    echo "[WEEKEND EXTRA] Restarting HTTPD..." | tee -a "$LOG_FILE"
    sudo /usr/sbin/httpd -k restart >> "$LOG_FILE" 2>&1
fi

echo "========== Restart Script Completed ==========" | tee -a "$LOG_FILE"
echo "Check Log: $LOG_FILE" | tee -a "$LOG_FILE"