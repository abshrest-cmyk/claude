#!/bin/bash
# ABN Legal Finder - Desktop Shortcut / Cron Script
# Runs with current month/year for specified state (default: NSW)
#
# Usage:
#   ./abn_legal_finder_cron.sh              # Current month, NSW
#   ./abn_legal_finder_cron.sh VIC          # Current month, Victoria
#   ./abn_legal_finder_cron.sh NSW 11 2024  # Specific month/year

# Parse arguments or use defaults
STATE="${1:-NSW}"
MONTH="${2:-$(date +%-m)}"
YEAR="${3:-$(date +%Y)}"

# Create directories
OUTPUT_DIR="$HOME/Documents/ABN_Legal_Finder"
LOG_DIR="$OUTPUT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run_$(date +%Y%m%d_%H%M%S).log"

echo "=============================================="
echo "ABN Legal Finder - Quick Run"
echo "=============================================="
echo "State: $STATE"
echo "Month: $MONTH"
echo "Year:  $YEAR"
echo "Log:   $LOG_FILE"
echo "=============================================="

# Run the script with unbuffered output for real-time progress
cd /home/user/claude
/usr/bin/python3 -u /home/user/claude/abn_legal_finder.py "$MONTH" "$YEAR" "$STATE" 2>&1 | tee "$LOG_FILE"

echo ""
echo "=============================================="
echo "Completed at $(date)"
echo "Results saved to: $OUTPUT_DIR"
echo "=============================================="
