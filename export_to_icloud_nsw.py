#!/usr/bin/env python3
"""
Export NSW Solicitor Data to iCloud Drive
Automatically syncs new solicitors to iCloud for mobile access
"""

import sys
import sqlite3
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("⚠️  openpyxl not installed - Excel export disabled")
    print("   Install with: pip3 install openpyxl")

DB_PATH = Path.home() / "projects" / "law_scraper" / "data" / "solicitors.db"
ICLOUD_PATH = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Law Firms"

def check_icloud():
    """Check if iCloud Drive is available"""
    if not ICLOUD_PATH.parent.exists():
        print(f"✗ iCloud Drive not found at: {ICLOUD_PATH.parent}")
        print("  Make sure iCloud Drive is enabled on your Mac")
        return False

    # Create Law Firms folder if it doesn't exist
    ICLOUD_PATH.mkdir(parents=True, exist_ok=True)
    return True

def check_database():
    """Check if database exists"""
    if not DB_PATH.exists():
        print(f"✗ Database not found: {DB_PATH}")
        print("  Run law_solicitor_tracker.py first")
        return False
    return True

def export_new_solicitors_csv():
    """Export new solicitors to CSV in iCloud"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT solicitor_name, firm_name, suburb, postcode, phone, email,
               specialisations, first_seen
        FROM solicitors
        WHERE is_new = 1
        ORDER BY first_seen DESC
    ''')

    results = cursor.fetchall()
    conn.close()

    if not results:
        print("ℹ️  No new solicitors to export")
        return None

    # Generate filename
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = ICLOUD_PATH / f"NSW_New_Solicitors_{timestamp}.csv"

    # Write CSV
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Solicitor Name', 'Firm Name', 'Suburb', 'Postcode',
            'Phone', 'Email', 'Specialisations', 'First Seen'
        ])

        # Data
        writer.writerows(results)

    print(f"✓ Exported {len(results)} new solicitors to CSV")
    print(f"  {filename}")
    return filename

def export_new_solicitors_excel():
    """Export new solicitors to Excel in iCloud with formatting"""
    if not EXCEL_AVAILABLE:
        return None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT solicitor_name, firm_name, suburb, postcode, phone, email,
               specialisations, first_seen
        FROM solicitors
        WHERE is_new = 1
        ORDER BY first_seen DESC
    ''')

    results = cursor.fetchall()
    conn.close()

    if not results:
        return None

    # Generate filename
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = ICLOUD_PATH / f"NSW_New_Solicitors_{timestamp}.xlsx"

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "New Solicitors"

    # Header styling
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    # Headers
    headers = [
        'Solicitor Name', 'Firm Name', 'Suburb', 'Postcode',
        'Phone', 'Email', 'Specialisations', 'First Seen'
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    # Data rows
    for row_idx, row_data in enumerate(results, 2):
        for col_idx, value in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)

    # Adjust column widths
    column_widths = [30, 30, 20, 10, 15, 30, 40, 12]
    for col_idx, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = width

    # Save
    wb.save(filename)

    print(f"✓ Exported {len(results)} new solicitors to Excel")
    print(f"  {filename}")
    return filename

def export_all_solicitors_excel():
    """Export all solicitors to Excel in iCloud"""
    if not EXCEL_AVAILABLE:
        return None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT solicitor_name, firm_name, suburb, postcode, phone, email,
               specialisations, first_seen, is_new
        FROM solicitors
        ORDER BY first_seen DESC
    ''')

    results = cursor.fetchall()
    conn.close()

    if not results:
        return None

    # Generate filename
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = ICLOUD_PATH / f"NSW_All_Solicitors_{timestamp}.xlsx"

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "All Solicitors"

    # Header styling
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    # Headers
    headers = [
        'Solicitor Name', 'Firm Name', 'Suburb', 'Postcode',
        'Phone', 'Email', 'Specialisations', 'First Seen', 'New'
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    # Data rows with highlighting for new entries
    new_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    for row_idx, row_data in enumerate(results, 2):
        is_new = row_data[-1]  # Last column is is_new

        for col_idx, value in enumerate(row_data[:-1], 1):  # Exclude is_new from display
            cell = ws.cell(row=row_idx, column=col_idx, value=value)

            # Highlight new entries
            if is_new:
                cell.fill = new_fill

        # Add "NEW" indicator in last column
        cell = ws.cell(row=row_idx, column=len(headers))
        cell.value = "NEW" if is_new else ""
        if is_new:
            cell.fill = new_fill
            cell.font = Font(bold=True)

    # Adjust column widths
    column_widths = [30, 30, 20, 10, 15, 30, 40, 12, 8]
    for col_idx, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = width

    # Save
    wb.save(filename)

    print(f"✓ Exported {len(results)} total solicitors to Excel")
    print(f"  {filename}")
    return filename

def export_summary_json():
    """Export summary statistics as JSON for mobile apps"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM solicitors")
    total_solicitors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM solicitors WHERE is_new = 1")
    new_solicitors = cursor.fetchone()[0]

    cursor.execute('''
        SELECT solicitor_name, firm_name, suburb, phone, first_seen
        FROM solicitors
        WHERE is_new = 1
        ORDER BY first_seen DESC
        LIMIT 50
    ''')

    recent_solicitors = []
    for row in cursor.fetchall():
        recent_solicitors.append({
            'name': row[0],
            'firm': row[1],
            'suburb': row[2],
            'phone': row[3],
            'first_seen': row[4]
        })

    conn.close()

    # Create summary
    summary = {
        'last_updated': datetime.now().isoformat(),
        'total_solicitors': total_solicitors,
        'new_solicitors': new_solicitors,
        'recent': recent_solicitors
    }

    # Save to iCloud
    filename = ICLOUD_PATH / "NSW_Solicitors_Summary.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"✓ Exported summary JSON")
    print(f"  {filename}")
    return filename

def cleanup_old_exports(days_to_keep=30):
    """Remove exports older than specified days"""
    cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
    deleted_count = 0

    for file in ICLOUD_PATH.glob("NSW_*.{csv,xlsx}"):
        if file.stat().st_mtime < cutoff_date:
            file.unlink()
            deleted_count += 1

    if deleted_count > 0:
        print(f"🗑️  Cleaned up {deleted_count} old export files")

def main():
    """Export data to iCloud Drive"""
    print("\n" + "=" * 60)
    print("NSW SOLICITOR TRACKER - iCloud Export")
    print("=" * 60 + "\n")

    # Check prerequisites
    if not check_database():
        sys.exit(1)

    if not check_icloud():
        sys.exit(1)

    # Export files
    try:
        # CSV export (always available)
        export_new_solicitors_csv()

        # Excel exports (if openpyxl available)
        if EXCEL_AVAILABLE:
            export_new_solicitors_excel()
            export_all_solicitors_excel()

        # JSON summary (for mobile/web apps)
        export_summary_json()

        # Cleanup old files
        cleanup_old_exports(days_to_keep=30)

        print("\n" + "=" * 60)
        print("✅ iCloud export complete!")
        print(f"📁 Files saved to: {ICLOUD_PATH}")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ Export failed: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
