# ABN Legal Finder - Setup Guide

## Overview
This script connects to the Australian Business Register (ABR) API to find newly registered legal businesses in NSW.

## Files Created
- `abn_legal_finder.py` - Main Python script
- `abn_legal_finder_cron.sh` - Wrapper script for automated execution
- `~/Documents/ABN_Legal_Finder/` - Output directory for CSV files and logs

## Manual Usage

Run the script manually with:
```bash
python3 /home/user/claude/abn_legal_finder.py <month> <year> <state>
```

Examples:
```bash
# Search October 2025 NSW registrations
python3 /home/user/claude/abn_legal_finder.py 10 2025 NSW

# Search November 2025 NSW registrations
python3 /home/user/claude/abn_legal_finder.py 11 2025 NSW

# Search for current month automatically
python3 /home/user/claude/abn_legal_finder.py $(date +%-m) $(date +%Y) NSW
```

## Automated Execution - Cron Job Setup

To run the script automatically every day at 8pm:

### Option 1: Using Crontab (Linux/Mac)

1. Open crontab editor:
   ```bash
   crontab -e
   ```

2. Add this line:
   ```
   0 20 * * * /home/user/claude/abn_legal_finder_cron.sh
   ```

3. Save and exit. The script will now run daily at 8pm.

### Option 2: Using Systemd Timer (Linux)

1. Create service file `/etc/systemd/system/abn-legal-finder.service`:
   ```ini
   [Unit]
   Description=ABN Legal Finder

   [Service]
   Type=oneshot
   ExecStart=/home/user/claude/abn_legal_finder_cron.sh
   User=user
   ```

2. Create timer file `/etc/systemd/system/abn-legal-finder.timer`:
   ```ini
   [Unit]
   Description=Run ABN Legal Finder daily at 8pm

   [Timer]
   OnCalendar=*-*-* 20:00:00
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

3. Enable and start the timer:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable abn-legal-finder.timer
   sudo systemctl start abn-legal-finder.timer
   ```

4. Check timer status:
   ```bash
   sudo systemctl status abn-legal-finder.timer
   systemctl list-timers abn-legal-finder*
   ```

### Option 3: Manual Cron Entry (if crontab command not available)

Add this line to `/etc/crontab` or `/var/spool/cron/crontabs/user`:
```
0 20 * * * user /home/user/claude/abn_legal_finder_cron.sh
```

## Output

### CSV Files
Results are saved to: `~/Documents/ABN_Legal_Finder/`

Filename format: `legal_businesses_NSW_YYYY_M_TIMESTAMP.csv`

CSV includes these columns:
- ABN
- Entity Name
- Business Names
- Trading Names
- Entity Type
- ABN Status
- State
- Postcode
- GST
- ACN
- ABN Status Date

### Log Files
Execution logs are saved to: `~/Documents/ABN_Legal_Finder/logs/`

Filename format: `cron_YYYYMMDD_HHMMSS.log`

## Legal Business Keywords
The script filters for entities containing any of these keywords (case-insensitive):
- lawyer
- law
- solicitor
- legal
- conveyancer
- conveyancing
- barrister
- attorney
- notary

## API Details
- Base URL: https://abr.business.gov.au/ABRXMLSearch/AbrXmlSearch.asmx
- Authentication GUID: 60ff3b3e-c2f4-4e9d-a086-78c396e7013d
- Method: SOAP POST requests with XML envelopes

## Troubleshooting

### Network Errors
If you encounter proxy or connection errors, check:
- Network connectivity
- Firewall settings
- Proxy configuration

### No Results
If no ABNs are found:
- Verify the month/year has data available
- Check if registrations exist for that period
- Try a different month

### API Errors
The ABR API may experience:
- Rate limiting
- Scheduled maintenance
- Service interruptions

## Verifying Cron Setup

Check if cron job is scheduled:
```bash
crontab -l
```

View recent execution logs:
```bash
ls -lt ~/Documents/ABN_Legal_Finder/logs/ | head -5
tail ~/Documents/ABN_Legal_Finder/logs/cron_*.log
```

## Testing

Test the script manually before relying on automation:
```bash
# Test with a recent month
python3 /home/user/claude/abn_legal_finder.py 11 2025 NSW

# Test the cron wrapper
/home/user/claude/abn_legal_finder_cron.sh

# Check the output
ls -la ~/Documents/ABN_Legal_Finder/
```
