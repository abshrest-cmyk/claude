#!/usr/bin/env python3
"""
NSW Solicitor Tracker - Mobile Web Interface
Simple Flask web server for mobile access
"""

import sys
import sqlite3
from datetime import datetime
from pathlib import Path

try:
    from flask import Flask, render_template_string, jsonify, request
except ImportError:
    print("Flask not installed. Install with: pip3 install flask")
    sys.exit(1)

DB_PATH = Path.home() / "projects" / "law_scraper" / "data" / "solicitors.db"

app = Flask(__name__)

# HTML Template (mobile-responsive)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NSW Solicitor Tracker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
            padding-bottom: 80px;
        }

        .header {
            background: linear-gradient(135deg, #366092 0%, #4a7ba7 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .header p {
            opacity: 0.9;
            font-size: 14px;
        }

        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            padding: 20px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .stat-number {
            font-size: 32px;
            font-weight: 700;
            color: #366092;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 13px;
            color: #86868b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .tabs {
            display: flex;
            background: white;
            margin: 0 20px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            border: none;
            background: white;
            color: #86868b;
            font-weight: 500;
            transition: all 0.3s;
        }

        .tab.active {
            background: #366092;
            color: white;
        }

        .content {
            padding: 20px;
        }

        .solicitor-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #366092;
        }

        .solicitor-card.new {
            border-left-color: #ffcc00;
            background: #fffef7;
        }

        .solicitor-name {
            font-size: 18px;
            font-weight: 600;
            color: #1d1d1f;
            margin-bottom: 10px;
        }

        .solicitor-detail {
            display: flex;
            align-items: center;
            margin: 8px 0;
            font-size: 14px;
            color: #515154;
        }

        .solicitor-detail .icon {
            width: 20px;
            margin-right: 10px;
        }

        .badge {
            display: inline-block;
            background: #ffcc00;
            color: #1d1d1f;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .search-box {
            background: white;
            margin: 0 20px 20px;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .search-box input {
            width: 100%;
            padding: 12px;
            border: 1px solid #d2d2d7;
            border-radius: 8px;
            font-size: 16px;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #86868b;
        }

        .empty {
            text-align: center;
            padding: 40px;
            color: #86868b;
        }

        .refresh-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: #366092;
            color: white;
            border: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            font-size: 24px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>NSW Solicitor Tracker</h1>
        <p id="last-update">Loading...</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-number" id="stat-total">-</div>
            <div class="stat-label">Total Solicitors</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="stat-new">-</div>
            <div class="stat-label">New This Week</div>
        </div>
    </div>

    <div class="search-box">
        <input type="text" id="search-input" placeholder="Search solicitors or firms...">
    </div>

    <div class="tabs">
        <button class="tab active" onclick="showTab('new')">New</button>
        <button class="tab" onclick="showTab('all')">All</button>
    </div>

    <div class="content" id="content">
        <div class="loading">Loading...</div>
    </div>

    <button class="refresh-btn" onclick="loadData()">↻</button>

    <script>
        let allSolicitors = [];
        let currentTab = 'new';

        async function loadData() {
            try {
                const response = await fetch('/api/solicitors');
                const data = await response.json();

                allSolicitors = data.solicitors;

                document.getElementById('stat-total').textContent = data.stats.total;
                document.getElementById('stat-new').textContent = data.stats.new;
                document.getElementById('last-update').textContent = 'Last updated: ' + data.last_update;

                renderSolicitors();
            } catch (error) {
                document.getElementById('content').innerHTML =
                    '<div class="empty">Failed to load data. Make sure the server is running.</div>';
            }
        }

        function showTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            renderSolicitors();
        }

        function renderSolicitors() {
            const searchTerm = document.getElementById('search-input').value.toLowerCase();

            let filtered = allSolicitors.filter(s => {
                if (currentTab === 'new' && !s.is_new) return false;
                if (searchTerm && !s.solicitor_name.toLowerCase().includes(searchTerm) &&
                    !s.firm_name.toLowerCase().includes(searchTerm)) return false;
                return true;
            });

            const content = document.getElementById('content');

            if (filtered.length === 0) {
                content.innerHTML = '<div class="empty">No solicitors found</div>';
                return;
            }

            content.innerHTML = filtered.map(s => `
                <div class="solicitor-card ${s.is_new ? 'new' : ''}">
                    <div class="solicitor-name">
                        ${s.solicitor_name}
                        ${s.is_new ? '<span class="badge">NEW</span>' : ''}
                    </div>
                    ${s.firm_name ? `<div class="solicitor-detail"><span class="icon">🏢</span>${s.firm_name}</div>` : ''}
                    ${s.suburb ? `<div class="solicitor-detail"><span class="icon">📍</span>${s.suburb}${s.postcode ? ' ' + s.postcode : ''}</div>` : ''}
                    ${s.phone ? `<div class="solicitor-detail"><span class="icon">📞</span><a href="tel:${s.phone}">${s.phone}</a></div>` : ''}
                    ${s.email ? `<div class="solicitor-detail"><span class="icon">✉️</span><a href="mailto:${s.email}">${s.email}</a></div>` : ''}
                    ${s.specialisations ? `<div class="solicitor-detail"><span class="icon">⚖️</span>${s.specialisations}</div>` : ''}
                    <div class="solicitor-detail"><span class="icon">📅</span>First seen: ${s.first_seen}</div>
                </div>
            `).join('');
        }

        document.getElementById('search-input').addEventListener('input', renderSolicitors);

        // Load data on page load
        loadData();

        // Auto-refresh every 5 minutes
        setInterval(loadData, 300000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Render main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/solicitors')
def api_solicitors():
    """API endpoint for solicitor data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM solicitors")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM solicitors WHERE is_new = 1")
        new = cursor.fetchone()[0]

        # Get all solicitors
        cursor.execute('''
            SELECT solicitor_name, firm_name, suburb, postcode, phone, email,
                   specialisations, first_seen, is_new
            FROM solicitors
            ORDER BY first_seen DESC
            LIMIT 1000
        ''')

        solicitors = []
        for row in cursor.fetchall():
            solicitors.append({
                'solicitor_name': row[0] or '',
                'firm_name': row[1] or '',
                'suburb': row[2] or '',
                'postcode': row[3] or '',
                'phone': row[4] or '',
                'email': row[5] or '',
                'specialisations': row[6] or '',
                'first_seen': row[7] or '',
                'is_new': bool(row[8])
            })

        conn.close()

        return jsonify({
            'stats': {
                'total': total,
                'new': new
            },
            'solicitors': solicitors,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    """Start web server"""
    if not DB_PATH.exists():
        print(f"✗ Database not found: {DB_PATH}")
        print("  Run law_solicitor_tracker.py first")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("NSW SOLICITOR TRACKER - Mobile Web Interface")
    print("=" * 60)
    print("\nStarting web server...")
    print("\n📱 Access from your phone:")
    print("   1. Make sure your phone is on the same WiFi network")
    print("   2. Open browser and go to: http://YOUR-MAC-IP:5000")
    print("\n💻 Access from this computer:")
    print("   http://localhost:5000")
    print("\nPress Ctrl+C to stop\n")
    print("=" * 60 + "\n")

    # Run server (accessible from other devices on network)
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()
