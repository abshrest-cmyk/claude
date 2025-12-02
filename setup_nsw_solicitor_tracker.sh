#!/bin/bash
# NSW Law Society Solicitor Tracker - Setup Script

echo "=========================================="
echo "NSW Solicitor Tracker - Setup"
echo "=========================================="
echo ""

# Navigate to project directory
PROJECT_DIR=~/projects/law_scraper
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data
mkdir -p logs
mkdir -p ~/Library/LaunchAgents

# Install Python dependencies
echo ""
echo "📦 Installing Python packages..."
echo "   This may take a few minutes..."
pip3 install --user requests beautifulsoup4 lxml selenium webdriver-manager openpyxl

# Copy scripts to project directory
echo ""
echo "📋 Setting up scripts..."
SCRIPT_SOURCE="$(dirname "$(readlink -f "$0")")"

if [ -f "${SCRIPT_SOURCE}/law_solicitor_tracker.py" ]; then
    cp "${SCRIPT_SOURCE}/law_solicitor_tracker.py" "$PROJECT_DIR/"
    cp "${SCRIPT_SOURCE}/query_solicitors.py" "$PROJECT_DIR/"
    cp "${SCRIPT_SOURCE}/notify_nsw.py" "$PROJECT_DIR/"
    cp "${SCRIPT_SOURCE}/export_to_icloud_nsw.py" "$PROJECT_DIR/"
fi

# Make scripts executable
echo ""
echo "🔧 Making scripts executable..."
chmod +x law_solicitor_tracker.py 2>/dev/null
chmod +x query_solicitors.py 2>/dev/null
chmod +x notify_nsw.py 2>/dev/null
chmod +x export_to_icloud_nsw.py 2>/dev/null

# Create iCloud folder
echo ""
echo "☁️ Creating iCloud folder..."
mkdir -p ~/Library/Mobile\ Documents/com~apple~CloudDocs/Law\ Firms

# Create desktop shortcut
echo ""
echo "🖥️ Creating desktop shortcut..."
cat > ~/Desktop/Run_NSW_Solicitor_Scraper.command << 'EOF'
#!/bin/bash
cd ~/projects/law_scraper
echo "=========================================="
echo "NSW Solicitor Tracker - Manual Run"
echo "=========================================="
echo ""
echo "Starting NSW Solicitor Scraper..."
echo ""
python3 law_solicitor_tracker.py
echo ""
echo "Exporting to iCloud..."
python3 export_to_icloud_nsw.py
echo ""
echo "Sending notifications..."
python3 notify_nsw.py
echo ""
echo "=========================================="
echo "Done! Press any key to close..."
read -n 1
EOF
chmod +x ~/Desktop/Run_NSW_Solicitor_Scraper.command

# Create daily automation (6:00 PM)
echo ""
echo "⏰ Setting up daily automation (6:00 PM)..."
cat > ~/Library/LaunchAgents/com.nsw.solicitortracker.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nsw.solicitortracker</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd ~/projects/law_scraper && /usr/bin/python3 law_solicitor_tracker.py && /usr/bin/python3 export_to_icloud_nsw.py && /usr/bin/python3 notify_nsw.py daily</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$HOME/projects/law_scraper</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>$HOME/projects/law_scraper/logs/scraper.log</string>

    <key>StandardErrorPath</key>
    <string>$HOME/projects/law_scraper/logs/scraper_error.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

# Load the automation
launchctl unload ~/Library/LaunchAgents/com.nsw.solicitortracker.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.nsw.solicitortracker.plist

# Create query shortcuts
echo ""
echo "🔍 Creating query shortcuts..."

cat > ~/Desktop/View_New_Solicitors.command << 'EOF'
#!/bin/bash
cd ~/projects/law_scraper
python3 query_solicitors.py new
echo ""
echo "Press any key to close..."
read -n 1
EOF
chmod +x ~/Desktop/View_New_Solicitors.command

cat > ~/Desktop/View_Solicitor_Stats.command << 'EOF'
#!/bin/bash
cd ~/projects/law_scraper
python3 query_solicitors.py stats
echo ""
echo "Press any key to close..."
read -n 1
EOF
chmod +x ~/Desktop/View_Solicitor_Stats.command

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📁 Project directory: $PROJECT_DIR"
echo ""
echo "📝 Files created:"
echo "   - law_solicitor_tracker.py (main scraper)"
echo "   - query_solicitors.py (view/export data)"
echo "   - notify_nsw.py (email/iMessage alerts)"
echo "   - export_to_icloud_nsw.py (iCloud sync)"
echo ""
echo "🖥️ Desktop shortcuts:"
echo "   - Run_NSW_Solicitor_Scraper.command"
echo "   - View_New_Solicitors.command"
echo "   - View_Solicitor_Stats.command"
echo ""
echo "⏰ Daily automation:"
echo "   - Runs at 6:00 PM daily"
echo "   - Check status: launchctl list | grep solicitor"
echo "   - View logs: tail -f $PROJECT_DIR/logs/scraper.log"
echo ""
echo "📝 NEXT STEPS:"
echo ""
echo "1. Configure notifications (optional):"
echo "   Edit: $PROJECT_DIR/notify_nsw.py"
echo "   Set your email/phone number for alerts"
echo ""
echo "2. Test the scraper:"
echo "   cd $PROJECT_DIR"
echo "   python3 law_solicitor_tracker.py"
echo ""
echo "3. View results:"
echo "   python3 query_solicitors.py stats"
echo "   python3 query_solicitors.py new"
echo ""
echo "4. Export to iCloud:"
echo "   python3 export_to_icloud_nsw.py"
echo "   Files will be in: ~/Library/Mobile Documents/com~apple~CloudDocs/Law Firms/"
echo ""
echo "5. Access from mobile:"
echo "   Open Files app > iCloud Drive > Law Firms folder"
echo "   Or use the web interface (see mobile_web.py)"
echo ""
echo "=========================================="
echo ""
