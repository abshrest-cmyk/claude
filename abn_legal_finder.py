#!/usr/bin/env python3
"""
ABN Legal Finder Script
Connects to Australian Business Register API to find newly registered legal businesses

Targeting strategy:
- NSW: most lucrative market (conveyancing spend) - cast a wide net including
  sole practitioners and conveyancers.
- WA: commercial work only - target larger firms (companies/partnerships),
  skip sole traders and conveyancers.
- Speed is the edge: daily mode tracks already-seen ABNs and surfaces only
  brand-new leads each run.
"""

import sys
import csv
import os
import re
import json
from datetime import datetime, date, timedelta
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

# API Configuration
ABR_BASE_URL = "https://abr.business.gov.au/ABRXMLSearch/AbrXmlSearch.asmx"
AUTH_GUID = "60ff3b3e-c2f4-4e9d-a086-78c396e7013d"

OUTPUT_DIR = Path.home() / "Documents" / "ABN_Legal_Finder"
SEEN_ABNS_FILE = OUTPUT_DIR / "seen_abns.json"

# Keyword sets (matched on word boundaries, case insensitive)
CONVEYANCING_KEYWORDS = ['conveyancer', 'conveyancers', 'conveyancing', 'settlements']
GENERAL_LEGAL_KEYWORDS = [
    'lawyer', 'lawyers', 'law', 'solicitor', 'solicitors', 'legal',
    'barrister', 'barristers', 'attorney', 'attorneys', 'notary',
]

# Entity types that indicate a sole practitioner rather than a firm
INDIVIDUAL_ENTITY_TYPES = ['individual', 'sole trader']

# Per-state targeting profiles
STATE_PROFILES = {
    'NSW': {
        # Conveyancing spend makes NSW the most lucrative market - take
        # everything legal, including individual conveyancers.
        'keywords': GENERAL_LEGAL_KEYWORDS + CONVEYANCING_KEYWORDS,
        'firms_only': False,
    },
    'WA': {
        # Only commercial work in WA - larger firms only, so skip
        # conveyancers and sole practitioners.
        'keywords': GENERAL_LEGAL_KEYWORDS,
        'firms_only': True,
    },
}
DEFAULT_PROFILE = {
    'keywords': GENERAL_LEGAL_KEYWORDS + CONVEYANCING_KEYWORDS,
    'firms_only': False,
}


def search_by_registration_event(state, month, year):
    """
    Search for ABNs registered in a specific month/year/state using SOAP
    Returns list of ABNs
    """
    # SOAP envelopes must POST to the base .asmx URL; the .asmx/Method
    # form is the HTTP-GET protocol endpoint and 500s on SOAP bodies
    endpoint = ABR_BASE_URL

    # SOAP XML Envelope
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SearchByRegistrationEvent xmlns="http://abr.business.gov.au/ABRXMLSearch/">
      <authenticationGuid>{AUTH_GUID}</authenticationGuid>
      <month>{month}</month>
      <year>{year}</year>
      <state>{state}</state>
      <postcode></postcode>
    </SearchByRegistrationEvent>
  </soap:Body>
</soap:Envelope>"""

    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://abr.business.gov.au/ABRXMLSearch/SearchByRegistrationEvent'
    }

    try:
        print(f"Searching for registrations in {state} for {month}/{year}...")
        response = requests.post(endpoint, data=soap_body, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse XML response - ABNs come back as lowercase <abn> elements
        # in the ABR default namespace
        root = ET.fromstring(response.content)
        ns = {'abr': 'http://abr.business.gov.au/ABRXMLSearch/'}

        abns = []
        for abn_elem in root.findall('.//abr:abnList/abr:abn', ns):
            if abn_elem.text:
                abns.append(abn_elem.text.replace(' ', ''))

        print(f"Found {len(abns)} registered ABNs")
        return abns

    except requests.exceptions.RequestException as e:
        print(f"Error searching registrations: {e}")
        return []
    except ET.ParseError as e:
        print(f"Error parsing XML response: {e}")
        return []


def search_by_abn(abn):
    """
    Get detailed information for a specific ABN using SOAP
    Returns dict with business details or None
    """
    endpoint = ABR_BASE_URL

    # SOAP XML Envelope
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SearchByABNv201408 xmlns="http://abr.business.gov.au/ABRXMLSearch/">
      <searchString>{abn}</searchString>
      <includeHistoricalDetails>N</includeHistoricalDetails>
      <authenticationGuid>{AUTH_GUID}</authenticationGuid>
    </SearchByABNv201408>
  </soap:Body>
</soap:Envelope>"""

    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://abr.business.gov.au/ABRXMLSearch/SearchByABNv201408'
    }

    try:
        response = requests.post(endpoint, data=soap_body, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse XML response (businessEntity201408 in ABR default namespace)
        root = ET.fromstring(response.content)
        ns = {'ns': 'http://abr.business.gov.au/ABRXMLSearch/'}

        entity = root.find('.//ns:businessEntity201408', ns)
        if entity is None:
            return None

        def text(path):
            elem = entity.find(path, ns)
            return elem.text.strip() if elem is not None and elem.text else ''

        details = {}

        details['ABN'] = text('ns:ABN/ns:identifierValue').replace(' ', '') or abn

        # Entity Name: organisation name for firms, legal name for individuals
        entity_name = text('ns:mainName/ns:organisationName')
        if not entity_name:
            given = text('ns:legalName/ns:givenName')
            family = text('ns:legalName/ns:familyName')
            entity_name = ' '.join(p for p in (given, family) if p)
        details['Entity Name'] = entity_name

        # Business Names (multiple possible)
        business_names = []
        for bn in entity.findall('ns:businessName/ns:organisationName', ns):
            if bn.text:
                business_names.append(bn.text.strip())
        details['Business Names'] = '; '.join(business_names)

        # Trading Names (multiple possible)
        trading_names = []
        for tn in entity.findall('ns:mainTradingName/ns:organisationName', ns):
            if tn.text:
                trading_names.append(tn.text.strip())
        details['Trading Names'] = '; '.join(trading_names)

        details['Entity Type'] = text('ns:entityType/ns:entityDescription')
        details['ABN Status'] = text('ns:entityStatus/ns:entityStatusCode')
        details['ABN Status Date'] = text('ns:entityStatus/ns:effectiveFrom')
        details['State'] = text('ns:mainBusinessPhysicalAddress/ns:stateCode')
        details['Postcode'] = text('ns:mainBusinessPhysicalAddress/ns:postcode')
        # GST element is present with an effectiveFrom date when registered
        # (ABR uses 0001-01-01 as a null date)
        gst = text('ns:goodsAndServicesTax/ns:effectiveFrom')
        details['GST'] = '' if gst == '0001-01-01' else gst
        details['ACN'] = text('ns:ASICNumber')

        return details

    except requests.exceptions.RequestException as e:
        print(f"Error fetching ABN {abn}: {e}")
        return None
    except ET.ParseError as e:
        print(f"Error parsing XML for ABN {abn}: {e}")
        return None


def matched_keywords(details, keywords):
    """
    Return the keywords found in the business names (word-boundary match,
    so 'law' matches 'Smith Law Pty Ltd' but not 'Lawson Plumbing')
    """
    search_text = ' '.join([
        details.get('Entity Name', ''),
        details.get('Business Names', ''),
        details.get('Trading Names', '')
    ]).lower()

    return [kw for kw in keywords
            if re.search(r'\b' + re.escape(kw) + r'\b', search_text)]


def is_individual(details):
    """
    Check if the entity is a sole practitioner rather than a firm
    """
    entity_type = details.get('Entity Type', '').lower()
    return any(t in entity_type for t in INDIVIDUAL_ENTITY_TYPES)


def score_lead(details, state):
    """
    Score and label a lead so the hottest ones sort to the top of the CSV.

    NSW conveyancing leads are the most lucrative; in WA only larger
    commercial firms matter, where a company structure (ACN) and GST
    registration are the best available size signals.
    """
    score = 0
    reasons = []

    keywords = details.get('Matched Keywords', '')

    if state == 'NSW':
        score += 30
        reasons.append('NSW market')
        if any(kw in keywords for kw in CONVEYANCING_KEYWORDS):
            score += 30
            reasons.append('conveyancing')

    if details.get('ACN'):
        score += 20
        reasons.append('incorporated')
    if details.get('GST', '').strip().lower() not in ('', 'n', 'no'):
        score += 10
        reasons.append('GST registered')
    if not is_individual(details):
        score += 10
        reasons.append('firm structure')

    if score >= 60:
        priority = 'HOT'
    elif score >= 40:
        priority = 'WARM'
    else:
        priority = 'STANDARD'

    return score, priority, ', '.join(reasons)


def load_seen_abns():
    """
    Load the set of ABNs surfaced in previous runs
    """
    try:
        with open(SEEN_ABNS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except (IOError, ValueError):
        return set()


def save_seen_abns(seen):
    """
    Persist the set of seen ABNs for future runs
    """
    SEEN_ABNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_ABNS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted(seen), f)


def find_legal_businesses(state, month, year, seen_abns=None):
    """
    Search one state/month and return scored legal business leads,
    skipping any ABNs already in seen_abns
    """
    profile = STATE_PROFILES.get(state, DEFAULT_PROFILE)

    abns = search_by_registration_event(state, month, year)
    if not abns:
        print("No ABNs found or error occurred")
        return []

    if seen_abns is not None:
        new_abns = [a for a in abns if a not in seen_abns]
        print(f"{len(new_abns)} of {len(abns)} ABNs are new since the last run")
        abns = new_abns

    leads = []
    for i, abn in enumerate(abns, 1):
        print(f"Processing ABN {i}/{len(abns)}: {abn}", end='\r')

        details = search_by_abn(abn)
        if not details:
            continue

        matches = matched_keywords(details, profile['keywords'])
        if not matches:
            continue

        # WA: only larger commercial firms are worth pursuing
        if profile['firms_only'] and is_individual(details):
            print(f"✗ Skipping sole practitioner ({state}): {details.get('Entity Name', 'N/A')[:50]}")
            continue

        details['Matched Keywords'] = ', '.join(matches)
        details['Search State'] = state
        score, priority, reasons = score_lead(details, state)
        details['Lead Score'] = score
        details['Priority'] = priority
        details['Priority Reasons'] = reasons

        leads.append(details)
        print(f"✓ {priority} lead found: {details.get('Entity Name', 'N/A')[:50]}")

    print()
    return leads


def save_to_csv(data, output_file):
    """
    Save business data to CSV file, hottest leads first
    """
    if not data:
        print("No data to save")
        return

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = sorted(data, key=lambda d: d.get('Lead Score', 0), reverse=True)

    # Define CSV columns
    columns = [
        'Priority', 'Lead Score', 'Priority Reasons', 'Search State',
        'ABN', 'Entity Name', 'Business Names', 'Trading Names',
        'Matched Keywords', 'Entity Type', 'ABN Status', 'State',
        'Postcode', 'GST', 'ACN', 'ABN Status Date'
    ]

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)

        print(f"Results saved to: {output_file}")
        print(f"Total legal businesses found: {len(data)}")

    except IOError as e:
        print(f"Error writing CSV file: {e}")


def run_daily():
    """
    Daily mode: sweep NSW and WA for the current month (and the previous
    month during the first week, since registrations land with a lag),
    surfacing only ABNs not seen in earlier runs.
    """
    today = date.today()
    periods = [(today.month, today.year)]
    if today.day <= 7:
        prev = today.replace(day=1) - timedelta(days=1)
        periods.append((prev.month, prev.year))

    seen_abns = load_seen_abns()
    all_leads = []

    for state in STATE_PROFILES:
        for month, year in periods:
            print("=" * 60)
            print(f"Daily sweep: {state} - {month}/{year}")
            print("=" * 60)
            leads = find_legal_businesses(state, month, year, seen_abns=seen_abns)
            all_leads.extend(leads)

    # Mark every new lead as seen so tomorrow's run only shows fresh firms
    for lead in all_leads:
        seen_abns.add(lead['ABN'])
    save_seen_abns(seen_abns)

    if all_leads:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_DIR / f"new_leads_{timestamp}.csv"
        save_to_csv(all_leads, output_file)
        hot = sum(1 for l in all_leads if l['Priority'] == 'HOT')
        print(f"{len(all_leads)} new leads ({hot} HOT)")
    else:
        print("No new leads today")


def main():
    """
    Main function
    """
    if len(sys.argv) == 2 and sys.argv[1] == 'daily':
        run_daily()
        return

    if len(sys.argv) != 4:
        print("Usage: python3 abn_legal_finder.py <month> <year> <state>")
        print("       python3 abn_legal_finder.py daily")
        print("Example: python3 abn_legal_finder.py 11 2025 NSW")
        sys.exit(1)

    month = sys.argv[1]
    year = sys.argv[2]
    state = sys.argv[3].upper()

    # Validate inputs
    try:
        month_int = int(month)
        year_int = int(year)
        if not (1 <= month_int <= 12):
            raise ValueError("Month must be between 1 and 12")
    except ValueError as e:
        print(f"Invalid month or year: {e}")
        sys.exit(1)

    profile = STATE_PROFILES.get(state, DEFAULT_PROFILE)

    print("=" * 60)
    print("ABN Legal Finder")
    print("=" * 60)
    print(f"Searching: {state} - {month}/{year}")
    print(f"Keywords: {', '.join(profile['keywords'])}")
    if profile['firms_only']:
        print("Filter: firms only (sole practitioners excluded)")
    print("=" * 60)

    legal_businesses = find_legal_businesses(state, month, year)

    print("=" * 60)

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"legal_businesses_{state}_{year}_{month}_{timestamp}.csv"

    save_to_csv(legal_businesses, output_file)
    print("=" * 60)


if __name__ == "__main__":
    main()
