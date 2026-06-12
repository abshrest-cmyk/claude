#!/bin/bash
# Cron wrapper script for ABN Legal Finder
# Runs the daily sweep across NSW and WA, surfacing only new leads

# Log file
LOG_DIR="$HOME/Documents/ABN_Legal_Finder/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cron_$(date +%Y%m%d_%H%M%S).log"

# Run the script and log output
echo "Running ABN Legal Finder daily sweep at $(date)" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"

cd /home/user/claude
/usr/bin/python3 /home/user/claude/abn_legal_finder.py daily >> "$LOG_FILE" 2>&1

echo "----------------------------------------" >> "$LOG_FILE"
echo "Completed at $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
