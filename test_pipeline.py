#!/usr/bin/env python3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from processors.cleaner import clean_record
from processors.normalizer import normalize_record
from processors.company_enrichment import enrich_company
from processors.deduplicator import deduplicate
from extractors.location_parser import enrich_record_with_location
from utils.schema_formatter import to_output_schema, OUTPUT_FIELDS


SAMPLE_RECORDS = [
    {
        "company_name": "TechCorp Solutions",
        "website": "https://techcorp.example.com",
        "email": "contact@techcorp.example.com",
        "phone": "+91 98765 43210",
        "address": "123 Industrial Area, Sector 62, Noida, Uttar Pradesh 201301, India",
        "industry": "technology",
        "description": "Leading software development company specializing in ERP solutions",
        "source": "google",
        "additional_info": "SAP certified partner since 2015",
    },
    {
        "company_name": "Global Manufacturing Ltd",
        "website": "www.globalmfg.com",
        "email": "sales@globalmfg.co.in",
        "phone": "91-22-27654321",
        "address": "Plot 45, MIDC, Andheri East, Mumbai, Maharashtra 400093",
        "industry": "manufacturing",
        "description": "Industrial equipment manufacturer and exporter",
        "source": "maps",
    },
    {
        "company_name": "Fresh Foods Pvt Ltd",
        "email": "info@freshfoods.example.com",
        "phone": "+919876543210",
        "address": "Near Railway Station, Ring Road, Surat, Gujarat",
        "industry": "food & beverage",
        "source": "website",
        "additional_info": "Located in Surat, Gujarat - organic food processing",
    },
    {
        "company_name": "Test Company",
        "website": "http://test.example.com",
        "email": "info@tempmail.com",
        "phone": "123",
        "source": "test",
    },
    {
        "company_name": "  ",
        "email": "invalid-email",
        "source": "test",
    },
]


def test_pipeline():
    print("=" * 70)
    print("PIPELINE TEST - Target Schema Validation")
    print("=" * 70)

    print("\n[1] Cleaning records...")
    cleaned = [clean_record(r) for r in SAMPLE_RECORDS]
    print(f"    Cleaned {len(cleaned)} records")

    print("\n[2] Normalizing records...")
    normalized = [normalize_record(r) for r in cleaned]
    print(f"    Normalized {len(normalized)} records")

    print("\n[3] Enriching companies...")
    enriched = [enrich_company(r) for r in normalized]
    print(f"    Enriched {len(enriched)} records")

    print("\n[4] Parsing locations...")
    with_locations = [enrich_record_with_location(r) for r in enriched]
    print(f"    Location parsing complete for {len(with_locations)} records")

    print("\n[5] Deduplicating...")
    unique = deduplicate(with_locations)
    print(f"    Deduplicated to {len(unique)} unique records")

    print("\n[6] Applying output schema...")
    output = to_output_schema(unique)
    print(f"    Final output: {len(output)} records")

    print("\n" + "=" * 70)
    print("OUTPUT SCHEMA VALIDATION")
    print("=" * 70)

    expected_fields = {
        "SL No.",
        "Company Name",
        "Website",
        "Email",
        "Phone",
        "Address",
        "City",
        "State",
        "Country",
        "Industry",
        "Description",
        "Source",
        "Additional Information",
    }

    if not output:
        print("ERROR: No output generated!")
        return False

    actual_fields = set(output[0].keys())
    print(f"\nExpected fields ({len(expected_fields)}):")
    for field in sorted(expected_fields):
        status = "✓" if field in actual_fields else "✗"
        print(f"    {status} {field}")

    extra_fields = actual_fields - expected_fields
    if extra_fields:
        print(f"\nExtra fields found: {extra_fields}")

    missing_fields = expected_fields - actual_fields
    if missing_fields:
        print(f"\nMissing fields: {missing_fields}")
        return False

    print("\n" + "=" * 70)
    print("SAMPLE OUTPUT (First Record)")
    print("=" * 70)
    for key, value in output[0].items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("FILTERED RECORDS (Invalid Data Removed)")
    print("=" * 70)
    for idx, rec in enumerate(output):
        issues = []
        if rec["Company Name"] == "Test Company":
            issues.append("generic company name")
        if rec["Email"] == "":
            issues.append("invalid email")
        if rec["Phone"] == "":
            issues.append("invalid phone")

        if issues:
            print(f"  Record {idx + 1}: Filtered out - {', '.join(issues)}")

    valid_records = [
        r for r in output if r["Company Name"] and r["Company Name"] != "Test Company"
    ]
    print(f"\n  Valid records remaining: {len(valid_records)}")

    print("\n" + "=" * 70)
    print("LOCATION PARSING VALIDATION")
    print("=" * 70)
    for rec in output:
        if rec["Company Name"]:
            city = rec.get("City", "N/A")
            state = rec.get("State", "N/A")
            country = rec.get("Country", "N/A")
            print(f"  {rec['Company Name']}: {city}, {state}, {country}")

    print("\n" + "=" * 70)
    if expected_fields == actual_fields:
        print("SUCCESS: Schema validation passed!")
        return True
    else:
        print("FAILURE: Schema mismatch detected!")
        return False


if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
