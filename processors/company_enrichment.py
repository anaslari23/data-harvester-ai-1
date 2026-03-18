from __future__ import annotations

import re
from typing import Any, Dict

from extractors.erp_extractor import detect_erp_name


EMPLOYEE_PATTERNS = [
    re.compile(r"(\d{1,6}\s*(?:\+|employees))", re.IGNORECASE),
    re.compile(r"(\d{1,6}\s*-\s*\d{1,6}\s*employees)", re.IGNORECASE),
]
TURNOVER_PATTERNS = [
    re.compile(
        r"((?:usd|inr|eur|gbp|\$|rs\.?)[\s\d,.]+(?:million|billion|crore|lakh)?)",
        re.IGNORECASE,
    ),
    re.compile(r"(annual revenue[^.]{0,80})", re.IGNORECASE),
    re.compile(r"(turnover[^.]{0,80})", re.IGNORECASE),
]
BRANCH_PATTERNS = [
    re.compile(r"(\d+\s*(?:branches|warehouses|locations|offices))", re.IGNORECASE),
]
INDUSTRY_KEYWORDS = {
    "Manufacturing": ["manufacturer", "manufacturing", "factory", "industrial"],
    "Retail": ["retail", "ecommerce", "store"],
    "Logistics": ["logistics", "warehouse", "supply chain", "freight"],
    "Healthcare": ["healthcare", "medical", "hospital", "pharma"],
    "Technology": ["software", "saas", "technology", "it services", "digital"],
    "Furniture": ["furniture", "interior", "home decor"],
    "Food & Beverage": ["food", "beverage", "biscuits", "snacks", "bakery"],
    "Mining": ["mica", "mining", "minerals"],
    "Education": ["education", "school", "college", "university", "training"],
    "Finance": ["finance", "banking", "insurance", "investment"],
    "Real Estate": ["real estate", "property", "construction", "building"],
    "Automotive": ["automotive", "vehicle", "car", "transportation"],
    "Agriculture": ["agriculture", "farming", "organic", "seeds"],
}


def _extract_first(patterns: list[re.Pattern[str]], text: str) -> str:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return " ".join(match.group(1).split())
    return ""


def _infer_industry(rec: Dict[str, Any], text: str) -> str:
    if rec.get("industry_type"):
        return str(rec["industry_type"])
    if rec.get("industry"):
        return str(rec["industry"])
    lower = text.lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            return industry
    return ""


def enrich_company(rec: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(rec)
    combined_text = " ".join(
        str(enriched.get(key, ""))
        for key in [
            "company_name",
            "industry",
            "description",
            "additional_info",
            "address",
        ]
    )

    if not enriched.get("industry_type"):
        enriched["industry_type"] = _infer_industry(enriched, combined_text)
    if not enriched.get("industry") and enriched.get("industry_type"):
        enriched["industry"] = enriched["industry_type"]

    if not enriched.get("description"):
        description_parts = []
        if enriched.get("additional_info"):
            desc_text = str(enriched["additional_info"])[:300]
            if len(desc_text) > 20:
                description_parts.append(desc_text)
        if description_parts:
            enriched["description"] = " ".join(description_parts)

    enriched.setdefault("city", "")
    enriched.setdefault("state", "")
    enriched.setdefault("country", "")
    enriched.setdefault("source", "")

    return enriched
