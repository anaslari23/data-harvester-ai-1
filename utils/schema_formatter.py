from __future__ import annotations

from typing import Any, Dict, Iterable, List


OUTPUT_FIELDS = [
    "SL No.",
    "Company Name",
    "Website",
    "Owner/ IT Head/ CEO/Finance Head Name",
    "Phone Number",
    "EMail Address",
    "Address",
    "City",
    "State",
    "Country",
    "Industry_Type",
    "Employee_No",
    "Branch/Warehouse_No",
    "Annual_Turnover",
    "Current_Use_ERP_Software_Name",
    "Description",
    "Additional_Information",
]


def to_output_schema(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for idx, rec in enumerate(records, start=1):
        mapped: Dict[str, str] = {
            "SL No.": str(idx),
            "Company Name": str(rec.get("company_name") or rec.get("name") or ""),
            "Website": str(rec.get("website") or ""),
            "Owner/ IT Head/ CEO/Finance Head Name": str(rec.get("contact_name") or ""),
            "Phone Number": str(rec.get("phone") or ""),
            "EMail Address": str(rec.get("email") or ""),
            "Address": str(rec.get("address") or ""),
            "City": str(rec.get("city") or ""),
            "State": str(rec.get("state") or ""),
            "Country": str(rec.get("country") or ""),
            "Industry_Type": str(rec.get("industry_type") or rec.get("industry") or ""),
            "Employee_No": str(rec.get("employee_count") or ""),
            "Branch/Warehouse_No": str(rec.get("branch_count") or ""),
            "Annual_Turnover": str(rec.get("turnover") or ""),
            "Current_Use_ERP_Software_Name": str(rec.get("erp_software") or ""),
            "Description": str(rec.get("description") or ""),
            "Additional_Information": str(rec.get("additional_info") or ""),
        }
        result.append(mapped)
    return result
