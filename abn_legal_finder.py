#!/usr/bin/env python3
"""
ABN Legal Finder Script
Connects to Australian Business Register API to find newly registered legal businesses
"""

import sys
import csv
import os
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

# API Configuration
ABR_BASE_URL = "https://abr.business.gov.au/ABRXMLSearch/AbrXmlSearch.asmx"
AUTH_GUID = "60ff3b3e-c2f4-4e9d-a086-78c396e7013d"

# Legal business keywords (case insensitive)
LEGAL_KEYWORDS = [
    'lawyer', 'law', 'solicitor', 'legal', 'conveyancer',
    'conveyancing', 'barrister', 'attorney', 'notary'
]

def search_by_registration_event(state, month, year):
    """
    Search for ABNs registered in a specific month/year/state using SOAP
    Returns list of ABNs
    """
    endpoint = f"{ABR_BASE_URL}/SearchByRegistrationEvent"

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

        # Parse XML response
        root = ET.fromstring(response.content)

        # Extract ABNs from response
        # Define namespaces
        ns = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'abr': 'http://abr.business.gov.au/ABRXMLSearch/'
        }

        abns = []

        # Try with namespace first
        for abn_elem in root.findall('.//abr:ABN', ns):
            if abn_elem.text:
                abns.append(abn_elem.text.replace(' ', ''))

        # Try without namespace
        if not abns:
            for abn_elem in root.findall('.//ABN'):
                if abn_elem.text:
                    abns.append(abn_elem.text.replace(' ', ''))

        print(f"Found {len(abns)} registered ABNs")
        return abns

    except requests.exceptions.RequestException as e:
        print(f"Error searching registrations: {e}")
        # Try GET method as fallback
        try:
            print("Trying GET method as fallback...")
            params = {
                'authenticationGuid': AUTH_GUID,
                'month': str(month),
                'year': str(year),
                'state': state,
                'postcode': ''
            }
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            abns = []
            for abn_elem in root.findall('.//ABN'):
                if abn_elem.text:
                    abns.append(abn_elem.text.replace(' ', ''))

            print(f"Found {len(abns)} registered ABNs (via GET)")
            return abns
        except Exception as e2:
            print(f"GET fallback also failed: {e2}")
            return []
    except ET.ParseError as e:
        print(f"Error parsing XML response: {e}")
        return []


def search_by_abn(abn):
    """
    Get detailed information for a specific ABN using SOAP
    Returns dict with business details or None
    """
    endpoint = f"{ABR_BASE_URL}/SearchByABNv201408"

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

        # Parse XML response
        root = ET.fromstring(response.content)

        # Define namespace
        ns = {
            'ns': 'http://abr.business.gov.au/ABRXMLSearch/'
        }

        # Extract business details
        details = {}

        # ABN
        abn_elem = root.find('.//ns:ABN', ns) or root.find('.//ABN')
        details['ABN'] = abn_elem.text.replace(' ', '') if abn_elem is not None and abn_elem.text else abn

        # Entity Name
        entity_name_elem = (root.find('.//ns:EntityName', ns) or
                           root.find('.//ns:MainName/ns:OrganisationName', ns) or
                           root.find('.//MainName/OrganisationName'))
        details['Entity Name'] = entity_name_elem.text if entity_name_elem is not None and entity_name_elem.text else ''

        # Business Names (multiple possible)
        business_names = []
        for bn in root.findall('.//ns:BusinessName', ns):
            if bn.text:
                business_names.append(bn.text)
        if not business_names:
            for bn in root.findall('.//BusinessName'):
                if bn.text:
                    business_names.append(bn.text)
        details['Business Names'] = '; '.join(business_names)

        # Trading Names (multiple possible)
        trading_names = []
        for tn in root.findall('.//ns:MainTradingName/ns:OrganisationName', ns):
            if tn.text:
                trading_names.append(tn.text)
        if not trading_names:
            for tn in root.findall('.//MainTradingName/OrganisationName'):
                if tn.text:
                    trading_names.append(tn.text)
        details['Trading Names'] = '; '.join(trading_names)

        # Entity Type
        entity_type_elem = (root.find('.//ns:EntityTypeName', ns) or
                           root.find('.//EntityTypeName'))
        details['Entity Type'] = entity_type_elem.text if entity_type_elem is not None and entity_type_elem.text else ''

        # ABN Status
        status_elem = (root.find('.//ns:ABNStatus', ns) or
                      root.find('.//ABNStatus'))
        details['ABN Status'] = status_elem.text if status_elem is not None and status_elem.text else ''

        # ABN Status Date
        status_date_elem = (root.find('.//ns:ABNStatusFromDate', ns) or
                           root.find('.//ABNStatusFromDate'))
        details['ABN Status Date'] = status_date_elem.text if status_date_elem is not None and status_date_elem.text else ''

        # State
        state_elem = (root.find('.//ns:AddressState', ns) or
                     root.find('.//AddressState'))
        details['State'] = state_elem.text if state_elem is not None and state_elem.text else ''

        # Postcode
        postcode_elem = (root.find('.//ns:AddressPostcode', ns) or
                        root.find('.//AddressPostcode'))
        details['Postcode'] = postcode_elem.text if postcode_elem is not None and postcode_elem.text else ''

        # GST
        gst_elem = (root.find('.//ns:GST', ns) or
                   root.find('.//GST'))
        details['GST'] = gst_elem.text if gst_elem is not None and gst_elem.text else ''

        # ACN
        acn_elem = (root.find('.//ns:ASICNumber', ns) or
                   root.find('.//ASICNumber'))
        details['ACN'] = acn_elem.text if acn_elem is not None and acn_elem.text else ''

        return details

    except requests.exceptions.RequestException as e:
        print(f"Error fetching ABN {abn}: {e}")
        return None
    except ET.ParseError as e:
        print(f"Error parsing XML for ABN {abn}: {e}")
        return None


def is_legal_business(details):
    """
    Check if business name contains legal keywords
    """
    # Combine all name fields to search
    search_text = ' '.join([
        details.get('Entity Name', ''),
        details.get('Business Names', ''),
        details.get('Trading Names', '')
    ]).lower()

    # Check if any legal keyword is present
    for keyword in LEGAL_KEYWORDS:
        if keyword in search_text:
            return True

    return False


def save_to_csv(data, output_file):
    """
    Save business data to CSV file
    """
    if not data:
        print("No data to save")
        return

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Define CSV columns
    columns = [
        'ABN', 'Entity Name', 'Business Names', 'Trading Names',
        'Entity Type', 'ABN Status', 'State', 'Postcode',
        'GST', 'ACN', 'ABN Status Date'
    ]

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(data)

        print(f"Results saved to: {output_file}")
        print(f"Total legal businesses found: {len(data)}")

    except IOError as e:
        print(f"Error writing CSV file: {e}")


def main():
    """
    Main function
    """
    if len(sys.argv) != 4:
        print("Usage: python3 abn_legal_finder.py <month> <year> <state>")
        print("Example: python3 abn_legal_finder.py 11 2025 NSW")
        sys.exit(1)

    month = sys.argv[1]
    year = sys.argv[2]
    state = sys.argv[3]

    # Validate inputs
    try:
        month_int = int(month)
        year_int = int(year)
        if not (1 <= month_int <= 12):
            raise ValueError("Month must be between 1 and 12")
    except ValueError as e:
        print(f"Invalid month or year: {e}")
        sys.exit(1)

    print("=" * 60)
    print("ABN Legal Finder")
    print("=" * 60)
    print(f"Searching: {state} - {month}/{year}")
    print(f"Keywords: {', '.join(LEGAL_KEYWORDS)}")
    print("=" * 60)

    # Step 1: Get list of new ABNs
    abns = search_by_registration_event(state, month, year)

    if not abns:
        print("No ABNs found or error occurred")
        sys.exit(0)

    # Step 2: Get details for each ABN and filter for legal businesses
    legal_businesses = []

    for i, abn in enumerate(abns, 1):
        print(f"Processing ABN {i}/{len(abns)}: {abn}", end='\r')

        details = search_by_abn(abn)

        if details and is_legal_business(details):
            legal_businesses.append(details)
            print(f"✓ Legal business found: {details.get('Entity Name', 'N/A')[:50]}...")

    print("\n" + "=" * 60)

    # Step 3: Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path.home() / "Documents" / "ABN_Legal_Finder"
    output_file = output_dir / f"legal_businesses_{state}_{year}_{month}_{timestamp}.csv"

    save_to_csv(legal_businesses, output_file)
    print("=" * 60)


if __name__ == "__main__":
    main()
