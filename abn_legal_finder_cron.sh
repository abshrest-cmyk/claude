#!/bin/bash
# Cron wrapper script for ABN Legal Finder
# Automatically runs with current month and year for NSW

# Get current month and year
MONTH=$(date +%-m)
YEAR=$(date +%Y)
STATE="NSW"

# Log file
LOG_DIR="$HOME/Documents/ABN_Legal_Finder/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cron_$(date +%Y%m%d_%H%M%S).log"

# Run the script and log output
echo "Running ABN Legal Finder at $(date)" >> "$LOG_FILE"
echo "Parameters: Month=$MONTH, Year=$YEAR, State=$STATE" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"

cd /home/user/claude
/usr/bin/python3 /home/user/claude/abn_legal_finder.py "$MONTH" "$YEAR" "$STATE" >> "$LOG_FILE" 2>&1

echo "----------------------------------------" >> "$LOG_FILE"
echo "Completed at $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
