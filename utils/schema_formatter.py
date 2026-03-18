from __future__ import annotations

from typing import Any, Dict, Iterable, List


OUTPUT_FIELDS = [
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
]


def to_output_schema(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for idx, rec in enumerate(records, start=1):
        mapped: Dict[str, str] = {
            "SL No.": str(idx),
            "Company Name": str(rec.get("company_name") or rec.get("name") or ""),
            "Website": str(rec.get("website") or ""),
            "Email": str(rec.get("email") or ""),
            "Phone": str(rec.get("phone") or ""),
            "Address": str(rec.get("address") or ""),
            "City": str(rec.get("city") or ""),
            "State": str(rec.get("state") or ""),
            "Country": str(rec.get("country") or ""),
            "Industry": str(rec.get("industry_type") or rec.get("industry") or ""),
            "Description": str(rec.get("description") or ""),
            "Source": str(rec.get("source") or ""),
            "Additional Information": str(rec.get("additional_info") or ""),
        }
        result.append(mapped)
    return result
