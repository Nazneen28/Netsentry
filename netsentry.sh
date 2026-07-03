#!/bin/bash

HOSTS_FILE="hosts.txt"
LOG_FILE="netsentry.log"

while IFS= read -r host; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    if ping -c 1 "$host" >/dev/null 2>&1; then
        echo "[$timestamp] $host : UP"
        echo "$timestamp,$host,UP" >> "$LOG_FILE"
    else
        echo "[$timestamp] $host : DOWN"
        echo "$timestamp,$host,DOWN" >> "$LOG_FILE"
        osascript -e "display notification \"$host is DOWN\" with title \"NetSentry Alert\""
    fi
done < "$HOSTS_FILE"

