# NSW Law Society Solicitor Tracker

Track new solicitors and law firms registered with the Law Society of NSW, with automatic iCloud sync and mobile access.

## Features

- 🔍 **Automated Scraping**: Daily tracking of new NSW solicitors
- 💾 **Local Database**: SQLite database for historical tracking
- ☁️ **iCloud Sync**: Automatic export to iCloud Drive
- 📱 **Mobile Access**: View data on iPhone/iPad via iCloud or web interface
- 📧 **Notifications**: Email, iMessage, and desktop alerts for new entries
- 📊 **Export Options**: CSV, Excel (XLSX), and JSON formats
- 🔎 **Search & Query**: Command-line tools for searching solicitors

## Installation

### Quick Setup (macOS)

Run the setup script to install everything automatically:

```bash
chmod +x setup_nsw_solicitor_tracker.sh
./setup_nsw_solicitor_tracker.sh
```

The setup script will:
- Create project directory (`~/projects/law_scraper`)
- Install Python dependencies
- Set up daily automation (runs at 6:00 PM)
- Create desktop shortcuts
- Configure iCloud sync folder

### Manual Setup

1. **Create project directory:**
   ```bash
   mkdir -p ~/projects/law_scraper
   cd ~/projects/law_scraper
   ```

2. **Install dependencies:**
   ```bash
   pip3 install requests beautifulsoup4 lxml selenium webdriver-manager openpyxl flask
   ```

3. **Copy scripts:**
   - `law_solicitor_tracker.py` - Main scraper
   - `query_solicitors.py` - Query tool
   - `export_to_icloud_nsw.py` - iCloud export
   - `notify_nsw.py` - Notifications
   - `mobile_web.py` - Web interface

4. **Make scripts executable:**
   ```bash
   chmod +x *.py
   ```

## Usage

### Running the Tracker

**Manual run:**
```bash
cd ~/projects/law_scraper
python3 law_solicitor_tracker.py
```

**Desktop shortcut:**
- Double-click `Run_NSW_Solicitor_Scraper.command` on your desktop

**Automated (daily at 6:00 PM):**
- Already configured by setup script
- Check status: `launchctl list | grep solicitor`

### Viewing Data

**Show statistics:**
```bash
python3 query_solicitors.py stats
```

**List new solicitors:**
```bash
python3 query_solicitors.py new 50
```

**Search for solicitors:**
```bash
python3 query_solicitors.py search "Smith"
python3 query_solicitors.py search "Herbert Smith"
```

**Export to CSV:**
```bash
python3 query_solicitors.py export csv
python3 query_solicitors.py export-new csv
```

**Export to JSON:**
```bash
python3 query_solicitors.py export json
```

### iCloud Export

Export data to iCloud Drive for mobile access:

```bash
python3 export_to_icloud_nsw.py
```

Files are saved to:
```
~/Library/Mobile Documents/com~apple~CloudDocs/Law Firms/
```

Exports include:
- `NSW_New_Solicitors_YYYY-MM-DD.xlsx` - New solicitors (Excel)
- `NSW_All_Solicitors_YYYY-MM-DD.xlsx` - All solicitors (Excel)
- `NSW_New_Solicitors_YYYY-MM-DD.csv` - New solicitors (CSV)
- `NSW_Solicitors_Summary.json` - JSON summary for apps

### Notifications

**Configure notifications:**
Edit `notify_nsw.py` and set your preferences:

```python
# Email notifications
EMAIL_ENABLED = True
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
EMAIL_TO = "recipient@example.com"

# iMessage notifications
IMESSAGE_ENABLED = True
IMESSAGE_PHONE = "+61400000000"

# Desktop notifications
NOTIFICATION_CENTER_ENABLED = True
```

**Send notifications:**
```bash
python3 notify_nsw.py          # Alert about new solicitors
python3 notify_nsw.py daily    # Daily summary
```

## Mobile Access

### Option 1: iCloud Drive (Recommended)

1. Export data: `python3 export_to_icloud_nsw.py`
2. On iPhone/iPad:
   - Open **Files** app
   - Go to **iCloud Drive** > **Law Firms**
   - View Excel/CSV files

### Option 2: Web Interface

Start the mobile web server:

```bash
python3 mobile_web.py
```

Access from your phone:
1. Find your Mac's IP address: `ifconfig | grep "inet "`
2. On your phone's browser: `http://YOUR-MAC-IP:5000`

Features:
- Mobile-responsive design
- Search functionality
- Filter by new/all solicitors
- Direct links to call/email

### Option 3: iOS Shortcuts

Create an iOS Shortcut to check new solicitors:

1. Open **Shortcuts** app on iPhone
2. Create new shortcut:
   - Add action: **Get File** from iCloud Drive
   - Select: `Law Firms/NSW_Solicitors_Summary.json`
   - Add action: **Get Dictionary from Input**
   - Add action: **Get Dictionary Value** for "new_solicitors"
   - Add action: **Show Result**

3. Add to Home Screen for quick access

### Option 4: SSH Access (Advanced)

From iPhone (using apps like Termius):

```bash
ssh user@your-mac.local
cd ~/projects/law_scraper
python3 query_solicitors.py stats
python3 query_solicitors.py new 20
```

## Automation

### Daily Schedule

The setup script configures daily automation at 6:00 PM:

```xml
<!-- ~/Library/LaunchAgents/com.nsw.solicitortracker.plist -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>18</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

**Change schedule:**
1. Edit the plist file
2. Reload: `launchctl unload ~/Library/LaunchAgents/com.nsw.solicitortracker.plist && launchctl load ~/Library/LaunchAgents/com.nsw.solicitortracker.plist`

**View logs:**
```bash
tail -f ~/projects/law_scraper/logs/scraper.log
tail -f ~/projects/law_scraper/logs/scraper_error.log
```

## Data Structure

### Database Schema

**solicitors table:**
- `solicitor_name` - Solicitor's full name
- `firm_name` - Law firm name
- `practice_type` - Type of practice
- `location` - Location/address
- `suburb` - Suburb
- `postcode` - Postcode
- `phone` - Contact phone
- `email` - Contact email
- `practicing_certificate` - Certificate number
- `specialisations` - Areas of specialization
- `first_seen` - Date first tracked
- `last_seen` - Date last seen
- `is_new` - Whether entry is new (last 7 days)

**law_firms table:**
- `firm_name` - Firm name
- `address` - Full address
- `suburb` - Suburb
- `postcode` - Postcode
- `phone` - Contact phone
- `email` - Contact email
- `website` - Website URL
- `practice_areas` - Areas of practice
- `num_solicitors` - Number of solicitors
- `first_seen` - Date first tracked
- `last_seen` - Date last seen
- `is_new` - Whether firm is new

### Export Formats

**CSV Format:**
```csv
Solicitor Name,Firm Name,Suburb,Postcode,Phone,Email,Specialisations,First Seen
John Smith,Smith & Associates,Sydney,2000,02 9000 0000,john@smith.com.au,Family Law,2025-12-01
```

**JSON Format:**
```json
{
  "last_updated": "2025-12-02T10:30:00",
  "total_solicitors": 1500,
  "new_solicitors": 25,
  "recent": [
    {
      "name": "John Smith",
      "firm": "Smith & Associates",
      "suburb": "Sydney",
      "phone": "02 9000 0000",
      "first_seen": "2025-12-01"
    }
  ]
}
```

## Troubleshooting

### "Database not found" error

Run the tracker first to initialize:
```bash
python3 law_solicitor_tracker.py
```

### "iCloud Drive not found" error

Ensure iCloud Drive is enabled:
1. System Settings > Apple ID > iCloud
2. Enable "iCloud Drive"

### Selenium/WebDriver errors

Install Chrome and ChromeDriver:
```bash
brew install --cask google-chrome
pip3 install --upgrade selenium webdriver-manager
```

### Email notifications not working

For Gmail:
1. Enable 2-factor authentication
2. Create an App Password: https://myaccount.google.com/apppasswords
3. Use the app password in `notify_nsw.py`

### Automation not running

Check launchd status:
```bash
launchctl list | grep solicitor
launchctl start com.nsw.solicitortracker
```

View error logs:
```bash
tail ~/projects/law_scraper/logs/scraper_error.log
```

## Customization

### Change tracking frequency

Edit the hours/minutes in:
```
~/Library/LaunchAgents/com.nsw.solicitortracker.plist
```

### Modify search criteria

Edit `law_solicitor_tracker.py`:
- Adjust `search_recent_solicitors()` function
- Modify date range (currently 30 days)
- Add filters for specific suburbs/postcodes

### Add custom fields

1. Modify database schema in `setup_database()`
2. Update `extract_solicitor_data()` to capture new fields
3. Update export functions in all scripts

## File Locations

```
~/projects/law_scraper/
├── data/
│   ├── solicitors.db              # SQLite database
│   └── *.csv, *.xlsx, *.json      # Exports
├── logs/
│   ├── tracker.log                # Application logs
│   ├── scraper.log                # Automation logs
│   └── scraper_error.log          # Error logs
└── *.py                           # Python scripts

~/Library/Mobile Documents/com~apple~CloudDocs/Law Firms/
├── NSW_New_Solicitors_*.xlsx      # Excel exports
├── NSW_All_Solicitors_*.xlsx
├── NSW_New_Solicitors_*.csv       # CSV exports
└── NSW_Solicitors_Summary.json    # JSON summary

~/Library/LaunchAgents/
└── com.nsw.solicitortracker.plist # Automation config

~/Desktop/
├── Run_NSW_Solicitor_Scraper.command
├── View_New_Solicitors.command
└── View_Solicitor_Stats.command
```

## Security & Privacy

- All data is stored locally on your Mac
- iCloud sync uses your personal iCloud account
- No third-party services except NSW Law Society website
- Email credentials stored in plain text (edit `notify_nsw.py` carefully)
- Database contains publicly available information from Law Society

## Legal

This tool accesses publicly available information from the NSW Law Society website. Ensure your use complies with:
- NSW Law Society Terms of Service
- Australian Privacy Act 1988
- Spam Act 2003 (if sending communications)

Do not use this data for:
- Unsolicited marketing
- Automated spam
- Harassment

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `~/projects/law_scraper/logs/`
3. Ensure all dependencies are installed
4. Test manually before relying on automation

## Sources

- [NSW Law Society Register of Solicitors](https://www.lawsociety.com.au/register-of-solicitors)
- [NSW Law Society Search Help](https://www.lawsociety.com.au/register-solicitors/register-solicitors-search-help)

## License

Personal use only. Respect the Law Society's terms of service.
