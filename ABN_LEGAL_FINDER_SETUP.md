# ABN Legal Finder - Setup Guide

## Overview
This script connects to the Australian Business Register (ABR) API to find newly registered legal businesses.

### Targeting strategy
- **NSW** (most lucrative - conveyancing spend): wide net, including conveyancers and sole practitioners.
- **WA** (commercial work only): larger firms only - sole practitioners and conveyancers are filtered out.
- **Speed edge**: the daily sweep remembers which ABNs it has already surfaced (`~/Documents/ABN_Legal_Finder/seen_abns.json`) and outputs only brand-new leads each run, sorted hottest-first with a `Priority` (HOT/WARM/STANDARD) and `Lead Score` column.

## Files Created
- `abn_legal_finder.py` - Main Python script
- `abn_legal_finder_cron.sh` - Wrapper script for automated execution
- `~/Documents/ABN_Legal_Finder/` - Output directory for CSV files and logs

## Manual Usage

Daily sweep (recommended - NSW + WA, new leads only):
```bash
python3 /home/user/claude/abn_legal_finder.py daily
```

Or search a single state/month (no de-duplication):
```bash
python3 /home/user/claude/abn_legal_finder.py <month> <year> <state>
```

Examples:
```bash
# Search November 2025 NSW registrations
python3 /home/user/claude/abn_legal_finder.py 11 2025 NSW

# Search November 2025 WA registrations (firms only)
python3 /home/user/claude/abn_legal_finder.py 11 2025 WA
```

During the first week of each month the daily sweep also re-checks the
previous month, since ABN registrations can appear with a lag.

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

Filename formats:
- Daily sweep: `new_leads_TIMESTAMP.csv` (NSW + WA combined, new leads only)
- Single search: `legal_businesses_STATE_YYYY_M_TIMESTAMP.csv`

Rows are sorted hottest lead first. CSV includes these columns:
- Priority (HOT / WARM / STANDARD)
- Lead Score
- Priority Reasons (e.g. "NSW market, conveyancing, incorporated")
- Search State
- ABN
- Entity Name
- Business Names
- Trading Names
- Matched Keywords
- Entity Type
- ABN Status
- State
- Postcode
- GST
- ACN
- ABN Status Date

### Lead scoring
- NSW lead: +30 (more lucrative market)
- Conveyancing keyword in NSW: +30
- Incorporated (has ACN): +20
- GST registered: +10
- Firm structure (not individual/sole trader): +10

HOT >= 60, WARM >= 40, otherwise STANDARD.

### Log Files
Execution logs are saved to: `~/Documents/ABN_Legal_Finder/logs/`

Filename format: `cron_YYYYMMDD_HHMMSS.log`

## Legal Business Keywords
Keywords are matched on word boundaries (so "law" matches "Smith Law Pty Ltd" but not "Lawson Plumbing"), case-insensitive.

NSW (and any other state): lawyer(s), law, solicitor(s), legal, barrister(s), attorney(s), notary, conveyancer(s), conveyancing, settlements

WA: same list **minus** the conveyancing keywords, and sole practitioners (Individual/Sole Trader entity types) are excluded - only firms doing commercial work are surfaced.

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
