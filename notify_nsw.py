#!/usr/bin/env python3
"""
NSW Solicitor Tracker - Notification System
Send alerts via email or iMessage when new solicitors are found
"""

import sys
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_PATH = Path.home() / "projects" / "law_scraper" / "data" / "solicitors.db"

# ==============================================================================
# CONFIGURATION - Edit these values
# ==============================================================================

# Email settings (for email notifications)
EMAIL_ENABLED = False  # Set to True to enable email notifications
SMTP_SERVER = "smtp.gmail.com"  # Gmail SMTP server
SMTP_PORT = 587  # TLS port
SMTP_USERNAME = "your-email@gmail.com"  # Your email
SMTP_PASSWORD = "your-app-password"  # Gmail app password (not regular password)
EMAIL_TO = "recipient@example.com"  # Where to send notifications

# iMessage settings (macOS only)
IMESSAGE_ENABLED = False  # Set to True to enable iMessage notifications
IMESSAGE_PHONE = "+61400000000"  # Your phone number (include country code)

# macOS Notification Center
NOTIFICATION_CENTER_ENABLED = True  # Desktop notifications (macOS)

# ==============================================================================

def check_database():
    """Check if database exists"""
    if not DB_PATH.exists():
        print(f"✗ Database not found: {DB_PATH}")
        return False
    return True

def get_new_solicitors():
    """Get list of new solicitors from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT solicitor_name, firm_name, suburb, phone, email, first_seen
        FROM solicitors
        WHERE is_new = 1
        ORDER BY first_seen DESC
    ''')

    results = cursor.fetchall()
    conn.close()

    return results

def send_email_notification(solicitors):
    """Send email notification about new solicitors"""
    if not EMAIL_ENABLED:
        return

    if not solicitors:
        print("ℹ️  No new solicitors to notify about")
        return

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"NSW Solicitor Alert: {len(solicitors)} New Solicitor{'s' if len(solicitors) > 1 else ''}"
        msg['From'] = SMTP_USERNAME
        msg['To'] = EMAIL_TO

        # Plain text version
        text_body = f"NSW Law Society Solicitor Tracker\n\n"
        text_body += f"Found {len(solicitors)} new solicitor(s):\n\n"

        for sol in solicitors[:20]:  # Limit to first 20
            name, firm, suburb, phone, email, first_seen = sol
            text_body += f"• {name}\n"
            if firm:
                text_body += f"  Firm: {firm}\n"
            if suburb:
                text_body += f"  Location: {suburb}\n"
            if phone:
                text_body += f"  Phone: {phone}\n"
            if email:
                text_body += f"  Email: {email}\n"
            text_body += "\n"

        if len(solicitors) > 20:
            text_body += f"\n... and {len(solicitors) - 20} more\n"

        # HTML version
        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; }}
              .header {{ background-color: #366092; color: white; padding: 15px; }}
              .solicitor {{ border-left: 3px solid #366092; padding: 10px; margin: 10px 0; background-color: #f5f5f5; }}
              .solicitor-name {{ font-weight: bold; font-size: 16px; color: #333; }}
              .detail {{ margin: 5px 0; color: #666; }}
            </style>
          </head>
          <body>
            <div class="header">
              <h2>NSW Solicitor Tracker Alert</h2>
              <p>Found {len(solicitors)} new solicitor{'s' if len(solicitors) > 1 else ''}</p>
            </div>
        """

        for sol in solicitors[:20]:
            name, firm, suburb, phone, email, first_seen = sol
            html_body += f'<div class="solicitor">'
            html_body += f'<div class="solicitor-name">{name}</div>'
            if firm:
                html_body += f'<div class="detail">🏢 Firm: {firm}</div>'
            if suburb:
                html_body += f'<div class="detail">📍 Location: {suburb}</div>'
            if phone:
                html_body += f'<div class="detail">📞 Phone: {phone}</div>'
            if email:
                html_body += f'<div class="detail">✉️ Email: {email}</div>'
            html_body += f'<div class="detail">📅 First Seen: {first_seen}</div>'
            html_body += '</div>'

        if len(solicitors) > 20:
            html_body += f'<p><i>... and {len(solicitors) - 20} more solicitors</i></p>'

        html_body += """
          </body>
        </html>
        """

        # Attach parts
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"✓ Email notification sent to {EMAIL_TO}")

    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        print("  Check your SMTP settings in notify_nsw.py")

def send_imessage_notification(solicitors):
    """Send iMessage notification (macOS only)"""
    if not IMESSAGE_ENABLED:
        return

    if not solicitors:
        return

    try:
        # Create message text
        message = f"NSW Solicitor Alert: {len(solicitors)} new solicitor(s) found"

        if len(solicitors) <= 3:
            message += "\n\n"
            for sol in solicitors:
                name, firm, suburb, _, _, _ = sol
                message += f"• {name}"
                if firm:
                    message += f" @ {firm}"
                if suburb:
                    message += f" ({suburb})"
                message += "\n"
        else:
            message += f"\n\nCheck your Mac for full list"

        # Send via AppleScript
        script = f'''
        tell application "Messages"
            set targetService to 1st service whose service type = iMessage
            set targetBuddy to buddy "{IMESSAGE_PHONE}" of targetService
            send "{message}" to targetBuddy
        end tell
        '''

        subprocess.run(['osascript', '-e', script], check=True)
        print(f"✓ iMessage sent to {IMESSAGE_PHONE}")

    except Exception as e:
        print(f"✗ Failed to send iMessage: {e}")
        print("  Make sure Messages app is configured on your Mac")

def send_notification_center(solicitors):
    """Send macOS Notification Center alert"""
    if not NOTIFICATION_CENTER_ENABLED:
        return

    if not solicitors:
        return

    try:
        count = len(solicitors)
        title = "NSW Solicitor Tracker"
        message = f"Found {count} new solicitor{'s' if count > 1 else ''}"

        # Show first solicitor name if only one
        if count == 1:
            name = solicitors[0][0]
            firm = solicitors[0][1]
            message = f"New: {name}"
            if firm:
                message += f" @ {firm}"

        # Use osascript to trigger notification
        script = f'display notification "{message}" with title "{title}" sound name "Glass"'
        subprocess.run(['osascript', '-e', script], check=True)

        print(f"✓ Desktop notification sent")

    except Exception as e:
        print(f"✗ Failed to send notification: {e}")

def send_daily_summary():
    """Send daily summary of activity"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get today's statistics
    today = datetime.now().date()

    cursor.execute('''
        SELECT COUNT(*) FROM solicitors
        WHERE DATE(first_seen) = ?
    ''', (today,))
    today_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM solicitors WHERE is_new = 1")
    new_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM solicitors")
    total_count = cursor.fetchone()[0]

    conn.close()

    # Only send if there's activity
    if today_count == 0 and new_count == 0:
        print("ℹ️  No activity today - skipping daily summary")
        return

    summary = f"""NSW Solicitor Tracker - Daily Summary

📅 Date: {today}

Today's Activity:
• New solicitors today: {today_count}
• Total new (last 7 days): {new_count}
• Total tracked: {total_count}

Check your iCloud Drive for detailed reports.
    """

    # Send via configured channels
    if NOTIFICATION_CENTER_ENABLED:
        try:
            script = f'display notification "Today: {today_count} new | Total: {new_count} new" with title "NSW Solicitor Tracker" subtitle "Daily Summary"'
            subprocess.run(['osascript', '-e', script], check=True)
            print("✓ Daily summary notification sent")
        except Exception as e:
            print(f"✗ Failed to send summary notification: {e}")

def main():
    """Send notifications based on command line argument"""
    print("\n" + "=" * 60)
    print("NSW SOLICITOR TRACKER - Notifications")
    print("=" * 60 + "\n")

    if not check_database():
        sys.exit(1)

    # Determine notification mode
    mode = sys.argv[1] if len(sys.argv) > 1 else "new"

    if mode == "daily":
        # Daily summary
        send_daily_summary()
    else:
        # Alert about new solicitors
        solicitors = get_new_solicitors()

        if not solicitors:
            print("ℹ️  No new solicitors to notify about")
            return

        print(f"📬 Sending notifications for {len(solicitors)} new solicitor(s)...\n")

        # Send via all enabled channels
        send_notification_center(solicitors)
        send_email_notification(solicitors)
        send_imessage_notification(solicitors)

    print("\n" + "=" * 60)
    print("✅ Notifications complete")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
