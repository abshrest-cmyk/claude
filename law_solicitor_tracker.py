#!/usr/bin/env python3
"""
NSW Law Society Solicitor Tracker
Tracks new solicitors and law firms registered with the Law Society of NSW
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import time

try:
    import requests
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Run: pip3 install requests beautifulsoup4 selenium webdriver-manager lxml")
    sys.exit(1)

# Configuration
BASE_URL = "https://www.lawsociety.com.au/register-of-solicitors"
DB_PATH = Path.home() / "projects" / "law_scraper" / "data" / "solicitors.db"
LOG_PATH = Path.home() / "projects" / "law_scraper" / "logs" / "tracker.log"

def setup_database():
    """Initialize SQLite database for tracking solicitors and firms"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Solicitors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solicitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solicitor_name TEXT NOT NULL,
            firm_name TEXT,
            practice_type TEXT,
            location TEXT,
            suburb TEXT,
            postcode TEXT,
            phone TEXT,
            email TEXT,
            practicing_certificate TEXT,
            specialisations TEXT,
            first_seen DATE NOT NULL,
            last_seen DATE NOT NULL,
            is_new BOOLEAN DEFAULT 1,
            UNIQUE(solicitor_name, firm_name)
        )
    ''')

    # Law firms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS law_firms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firm_name TEXT NOT NULL UNIQUE,
            address TEXT,
            suburb TEXT,
            postcode TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            practice_areas TEXT,
            num_solicitors INTEGER,
            first_seen DATE NOT NULL,
            last_seen DATE NOT NULL,
            is_new BOOLEAN DEFAULT 1
        )
    ''')

    # Tracking history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            solicitors_found INTEGER,
            firms_found INTEGER,
            new_solicitors INTEGER,
            new_firms INTEGER,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✓ Database initialized")

def log_message(message):
    """Log message to file and console"""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"

    print(message)
    with open(LOG_PATH, 'a') as f:
        f.write(log_entry)

def setup_selenium_driver(headless=True):
    """Configure and return Selenium WebDriver"""
    chrome_options = Options()

    if headless:
        chrome_options.add_argument('--headless')

    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        log_message("✓ Selenium WebDriver initialized")
        return driver
    except Exception as e:
        log_message(f"✗ Failed to initialize WebDriver: {e}")
        return None

def search_recent_solicitors(driver, days_back=30):
    """
    Search for solicitors registered in recent days
    This is a simplified approach - you may need to adjust based on actual site structure
    """
    solicitors = []

    try:
        log_message(f"Searching for solicitors from last {days_back} days...")
        driver.get(BASE_URL)

        # Wait for page to load
        time.sleep(3)

        # Try to find and interact with search form
        # NOTE: You'll need to inspect the actual page and update these selectors
        try:
            # Look for search tabs or form
            wait = WebDriverWait(driver, 10)

            # This is a placeholder - update with actual selectors from the site
            # Example: search by recently registered
            # search_input = wait.until(EC.presence_of_element_located((By.ID, "search-input")))
            # search_input.send_keys("solicitor")

            # For now, we'll scrape the visible content
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract solicitor listings (adjust selectors based on actual page)
            # This is a simplified example
            listings = soup.find_all(['div', 'tr'], class_=lambda x: x and 'solicitor' in x.lower() if x else False)

            log_message(f"Found {len(listings)} potential entries on page")

            # Parse listings
            for listing in listings[:50]:  # Limit to first 50 for now
                solicitor_data = extract_solicitor_data(listing)
                if solicitor_data:
                    solicitors.append(solicitor_data)

        except Exception as e:
            log_message(f"Search interaction failed: {e}")
            log_message("Tip: Update the selectors in the script to match the actual website structure")

    except Exception as e:
        log_message(f"Error during search: {e}")

    return solicitors

def extract_solicitor_data(element):
    """Extract solicitor information from HTML element"""
    try:
        # This is a placeholder - adjust based on actual HTML structure
        data = {
            'solicitor_name': element.get_text(strip=True),
            'firm_name': '',
            'practice_type': '',
            'location': '',
            'suburb': '',
            'postcode': '',
            'phone': '',
            'email': '',
            'practicing_certificate': '',
            'specialisations': ''
        }

        # Only return if we have at least a name
        if data['solicitor_name']:
            return data

    except Exception as e:
        log_message(f"Error extracting data: {e}")

    return None

def save_solicitor(conn, solicitor_data):
    """Save or update solicitor in database"""
    cursor = conn.cursor()
    today = datetime.now().date()

    try:
        # Check if solicitor exists
        cursor.execute('''
            SELECT id, first_seen FROM solicitors
            WHERE solicitor_name = ? AND firm_name = ?
        ''', (solicitor_data['solicitor_name'], solicitor_data.get('firm_name', '')))

        existing = cursor.fetchone()

        if existing:
            # Update last_seen
            cursor.execute('''
                UPDATE solicitors
                SET last_seen = ?, is_new = 0
                WHERE id = ?
            ''', (today, existing[0]))
            return False  # Not new
        else:
            # Insert new solicitor
            cursor.execute('''
                INSERT INTO solicitors (
                    solicitor_name, firm_name, practice_type, location,
                    suburb, postcode, phone, email, practicing_certificate,
                    specialisations, first_seen, last_seen, is_new
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                solicitor_data['solicitor_name'],
                solicitor_data.get('firm_name', ''),
                solicitor_data.get('practice_type', ''),
                solicitor_data.get('location', ''),
                solicitor_data.get('suburb', ''),
                solicitor_data.get('postcode', ''),
                solicitor_data.get('phone', ''),
                solicitor_data.get('email', ''),
                solicitor_data.get('practicing_certificate', ''),
                solicitor_data.get('specialisations', ''),
                today,
                today
            ))
            return True  # Is new

    except Exception as e:
        log_message(f"Error saving solicitor: {e}")
        return False

def mark_old_entries_not_new(conn):
    """Mark entries older than 7 days as not new"""
    cursor = conn.cursor()
    cutoff_date = datetime.now().date() - timedelta(days=7)

    cursor.execute('''
        UPDATE solicitors
        SET is_new = 0
        WHERE first_seen < ?
    ''', (cutoff_date,))

    cursor.execute('''
        UPDATE law_firms
        SET is_new = 0
        WHERE first_seen < ?
    ''', (cutoff_date,))

    conn.commit()

def run_tracking():
    """Main tracking function"""
    log_message("=" * 60)
    log_message("NSW Law Society Solicitor Tracker")
    log_message("=" * 60)

    # Setup
    setup_database()

    # Initialize Selenium
    driver = setup_selenium_driver(headless=True)
    if not driver:
        log_message("✗ Cannot proceed without WebDriver")
        return

    try:
        # Search for recent solicitors
        solicitors = search_recent_solicitors(driver, days_back=30)

        # Save to database
        conn = sqlite3.connect(DB_PATH)
        new_count = 0

        for solicitor in solicitors:
            if save_solicitor(conn, solicitor):
                new_count += 1
                log_message(f"✓ New solicitor: {solicitor['solicitor_name']}")

        # Mark old entries
        mark_old_entries_not_new(conn)

        # Log tracking history
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tracking_history (
                solicitors_found, new_solicitors, status
            ) VALUES (?, ?, ?)
        ''', (len(solicitors), new_count, 'success'))

        conn.commit()
        conn.close()

        log_message("=" * 60)
        log_message(f"✓ Tracking complete")
        log_message(f"  Total found: {len(solicitors)}")
        log_message(f"  New entries: {new_count}")
        log_message("=" * 60)

    except Exception as e:
        log_message(f"✗ Error during tracking: {e}")

    finally:
        driver.quit()

def main():
    """Entry point"""
    try:
        run_tracking()
    except KeyboardInterrupt:
        log_message("\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_message(f"✗ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
