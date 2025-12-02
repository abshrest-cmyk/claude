#!/usr/bin/env python3
"""
NSW Law Society Solicitor Query Tool
View, search, and export solicitor data
"""

import sys
import sqlite3
import csv
from datetime import datetime, timedelta
from pathlib import Path
import json

DB_PATH = Path.home() / "projects" / "law_scraper" / "data" / "solicitors.db"

def check_database():
    """Check if database exists"""
    if not DB_PATH.exists():
        print(f"✗ Database not found: {DB_PATH}")
        print("  Run law_solicitor_tracker.py first to initialize")
        sys.exit(1)

def show_stats():
    """Display database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("NSW SOLICITOR TRACKER - STATISTICS")
    print("=" * 60)

    # Total solicitors
    cursor.execute("SELECT COUNT(*) FROM solicitors")
    total_solicitors = cursor.fetchone()[0]
    print(f"\n📊 Total Solicitors: {total_solicitors}")

    # New solicitors (last 7 days)
    cursor.execute("SELECT COUNT(*) FROM solicitors WHERE is_new = 1")
    new_solicitors = cursor.fetchone()[0]
    print(f"✨ New Solicitors (last 7 days): {new_solicitors}")

    # Total firms
    cursor.execute("SELECT COUNT(*) FROM law_firms")
    total_firms = cursor.fetchone()[0]
    print(f"\n🏢 Total Law Firms: {total_firms}")

    # New firms
    cursor.execute("SELECT COUNT(*) FROM law_firms WHERE is_new = 1")
    new_firms = cursor.fetchone()[0]
    print(f"✨ New Firms (last 7 days): {new_firms}")

    # Recent activity
    print("\n📅 Recent Activity:")
    cursor.execute('''
        SELECT run_date, solicitors_found, new_solicitors, status
        FROM tracking_history
        ORDER BY run_date DESC
        LIMIT 5
    ''')

    for row in cursor.fetchall():
        date, found, new, status = row
        print(f"   {date}: {found} found, {new} new ({status})")

    # Top suburbs
    print("\n🗺️  Top Suburbs:")
    cursor.execute('''
        SELECT suburb, COUNT(*) as count
        FROM solicitors
        WHERE suburb IS NOT NULL AND suburb != ''
        GROUP BY suburb
        ORDER BY count DESC
        LIMIT 10
    ''')

    for row in cursor.fetchall():
        suburb, count = row
        print(f"   {suburb}: {count}")

    print("\n" + "=" * 60 + "\n")
    conn.close()

def list_new_solicitors(limit=50):
    """List recently added solicitors"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT solicitor_name, firm_name, suburb, phone, email, first_seen
        FROM solicitors
        WHERE is_new = 1
        ORDER BY first_seen DESC
        LIMIT ?
    ''', (limit,))

    results = cursor.fetchall()

    print("\n" + "=" * 60)
    print(f"NEW SOLICITORS (Last {limit})")
    print("=" * 60 + "\n")

    if not results:
        print("No new solicitors found")
    else:
        for row in results:
            name, firm, suburb, phone, email, first_seen = row
            print(f"👤 {name}")
            if firm:
                print(f"   Firm: {firm}")
            if suburb:
                print(f"   Location: {suburb}")
            if phone:
                print(f"   Phone: {phone}")
            if email:
                print(f"   Email: {email}")
            print(f"   First Seen: {first_seen}")
            print()

    conn.close()

def search_solicitors(query):
    """Search for solicitors by name or firm"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    search_pattern = f"%{query}%"

    cursor.execute('''
        SELECT solicitor_name, firm_name, suburb, postcode, phone, email, specialisations
        FROM solicitors
        WHERE solicitor_name LIKE ? OR firm_name LIKE ?
        ORDER BY solicitor_name
        LIMIT 100
    ''', (search_pattern, search_pattern))

    results = cursor.fetchall()

    print("\n" + "=" * 60)
    print(f"SEARCH RESULTS: '{query}'")
    print("=" * 60 + "\n")

    if not results:
        print(f"No solicitors found matching '{query}'")
    else:
        print(f"Found {len(results)} results:\n")
        for row in results:
            name, firm, suburb, postcode, phone, email, specialisations = row
            print(f"👤 {name}")
            if firm:
                print(f"   Firm: {firm}")
            if suburb:
                print(f"   Location: {suburb} {postcode}")
            if phone:
                print(f"   Phone: {phone}")
            if email:
                print(f"   Email: {email}")
            if specialisations:
                print(f"   Specialisations: {specialisations}")
            print()

    conn.close()

def export_to_csv(output_file=None, new_only=False):
    """Export solicitors to CSV"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Generate default filename if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path.home() / "projects" / "law_scraper" / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        prefix = "new_solicitors" if new_only else "all_solicitors"
        output_file = output_dir / f"{prefix}_{timestamp}.csv"

    # Query
    if new_only:
        cursor.execute('''
            SELECT solicitor_name, firm_name, practice_type, location, suburb,
                   postcode, phone, email, practicing_certificate, specialisations,
                   first_seen, last_seen
            FROM solicitors
            WHERE is_new = 1
            ORDER BY first_seen DESC
        ''')
    else:
        cursor.execute('''
            SELECT solicitor_name, firm_name, practice_type, location, suburb,
                   postcode, phone, email, practicing_certificate, specialisations,
                   first_seen, last_seen
            FROM solicitors
            ORDER BY first_seen DESC
        ''')

    results = cursor.fetchall()

    if not results:
        print("No data to export")
        conn.close()
        return

    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Solicitor Name', 'Firm Name', 'Practice Type', 'Location',
            'Suburb', 'Postcode', 'Phone', 'Email', 'Practicing Certificate',
            'Specialisations', 'First Seen', 'Last Seen'
        ])

        # Data
        writer.writerows(results)

    print(f"\n✓ Exported {len(results)} solicitors to: {output_file}\n")
    conn.close()
    return str(output_file)

def export_to_json(output_file=None, new_only=False):
    """Export solicitors to JSON"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Generate default filename if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path.home() / "projects" / "law_scraper" / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        prefix = "new_solicitors" if new_only else "all_solicitors"
        output_file = output_dir / f"{prefix}_{timestamp}.json"

    # Query
    if new_only:
        cursor.execute('''
            SELECT solicitor_name, firm_name, practice_type, location, suburb,
                   postcode, phone, email, practicing_certificate, specialisations,
                   first_seen, last_seen
            FROM solicitors
            WHERE is_new = 1
            ORDER BY first_seen DESC
        ''')
    else:
        cursor.execute('''
            SELECT solicitor_name, firm_name, practice_type, location, suburb,
                   postcode, phone, email, practicing_certificate, specialisations,
                   first_seen, last_seen
            FROM solicitors
            ORDER BY first_seen DESC
        ''')

    results = cursor.fetchall()

    if not results:
        print("No data to export")
        conn.close()
        return

    # Convert to list of dicts
    solicitors = []
    for row in results:
        solicitors.append({
            'solicitor_name': row[0],
            'firm_name': row[1],
            'practice_type': row[2],
            'location': row[3],
            'suburb': row[4],
            'postcode': row[5],
            'phone': row[6],
            'email': row[7],
            'practicing_certificate': row[8],
            'specialisations': row[9],
            'first_seen': row[10],
            'last_seen': row[11]
        })

    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(solicitors, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Exported {len(results)} solicitors to: {output_file}\n")
    conn.close()
    return str(output_file)

def show_usage():
    """Display usage information"""
    print("""
NSW Law Society Solicitor Query Tool

Usage:
    python3 query_solicitors.py <command> [options]

Commands:
    stats                   Show database statistics
    new [limit]            List new solicitors (default: 50)
    search <query>         Search solicitors by name or firm
    export [csv|json]      Export all solicitors (default: csv)
    export-new [csv|json]  Export new solicitors only

Examples:
    python3 query_solicitors.py stats
    python3 query_solicitors.py new 25
    python3 query_solicitors.py search "Smith"
    python3 query_solicitors.py export csv
    python3 query_solicitors.py export-new json
    """)

def main():
    """Entry point"""
    check_database()

    if len(sys.argv) < 2:
        show_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "stats":
        show_stats()

    elif command == "new":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        list_new_solicitors(limit)

    elif command == "search":
        if len(sys.argv) < 3:
            print("✗ Please provide a search query")
            sys.exit(1)
        query = ' '.join(sys.argv[2:])
        search_solicitors(query)

    elif command == "export":
        format_type = sys.argv[2] if len(sys.argv) > 2 else 'csv'
        if format_type == 'json':
            export_to_json(new_only=False)
        else:
            export_to_csv(new_only=False)

    elif command == "export-new":
        format_type = sys.argv[2] if len(sys.argv) > 2 else 'csv'
        if format_type == 'json':
            export_to_json(new_only=True)
        else:
            export_to_csv(new_only=True)

    else:
        print(f"✗ Unknown command: {command}")
        show_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()
