#!/bin/bash
# ABN Legal Finder - Double-click to run!
# Finds newly registered law firms in Australia

# Where your script lives
SCRIPT_DIR="$HOME/Documents/ABN_Legal_Finder"
SCRIPT="$SCRIPT_DIR/abn_legal_finder.py"

# Default settings (change these if you want)
STATE="NSW"
MONTH=$(date +%-m)
YEAR=$(date +%Y)

# Create output folder if needed
mkdir -p "$SCRIPT_DIR/logs"

clear
echo "=============================================="
echo "   ABN Legal Finder"
echo "=============================================="
echo ""
echo "  State: $STATE"
echo "  Month: $MONTH"
echo "  Year:  $YEAR"
echo ""
echo "=============================================="
echo ""

# Run the script
cd "$SCRIPT_DIR"
python3 -u "$SCRIPT" "$MONTH" "$YEAR" "$STATE"

echo ""
echo "=============================================="
echo "  Done! Check Documents/ABN_Legal_Finder for results"
echo "=============================================="
echo ""
echo "Press any key to close..."
read -n 1
