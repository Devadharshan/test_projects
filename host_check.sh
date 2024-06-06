#!/bin/bash

# Function to check disk space
check_disk_space() {
    hostname=$1
    threshold=$2
    echo "Checking disk space on $hostname..."
    disk_space=$(ssh $hostname df -h | awk '{print $5}' | sed 's/%//g' | tail -n +2)

    while read -r usage; do
        if [ $usage -gt $threshold ]; then
            echo "Disk space on $hostname is over $threshold%."
            echo "Listing files consuming the most space..."
            ssh $hostname sudo du -ah / | sort -rh | head -n 10
            # Assuming you have a way to push the output to Grafana, do it here
            # For example: curl -X POST -d "message=Disk space on $hostname is over $threshold%." http://grafana-server/api
        else
            echo "Disk space on $hostname is below $threshold%."
        fi
    done <<< "$disk_space"
}

# Set your hosts and threshold here
hosts=("host1" "host2" "host3")
threshold=80

# Loop through each host and check disk space
for host in "${hosts[@]}"; do
    check_disk_space $host $threshold
done