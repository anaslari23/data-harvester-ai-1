from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from extractors.erp_extractor import detect_erp_name
from extractors.rule_extractor import extract_employee_count as extract_emp_count
from extractors.rule_extractor import extract_turnover as extract_turn
from extractors.rule_extractor import extract_erp_from_text


EMPLOYEE_PATTERNS = [
    re.compile(r"(\d{1,6}\s*(?:\+|employees|employee))", re.IGNORECASE),
    re.compile(
        r"(\d{1,3}(?:,\d{3})*(?:\s*(?:to|-)\s*\d{1,6})?\s*employees?)", re.IGNORECASE
    ),
    re.compile(r"(?:team\s+(?:of\s+)?)(\d{1,6})", re.IGNORECASE),
    re.compile(r"(?:workforce\s+(?:of\s+)?)(\d{1,6})", re.IGNORECASE),
]

TURNOVER_PATTERNS = [
    re.compile(
        r"(?:annual\s+)?(?:revenue|turnover|sales)(?:\s+(?:of|is|:))?\s*(?:inr|usd|eur|gbp|\$|rs\.?|inr\.?)?\s*([\d,\.]+(?:\s*(?:crore|lakh|million|billion|thousand))?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:inr|usd|eur|gbp|\$|rs\.?)\s*([\d,\.]+(?:\s*(?:crore|lakh|million|billion|thousand))?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"turnover(?:\s+(?:of|is|:))?\s*(?:inr|usd)?\s*([\d,\.]+)", re.IGNORECASE
    ),
]

BRANCH_PATTERNS = [
    re.compile(
        r"(\d+)\s*(?:branches|branch|warehouses|warehouse|locations|location|offices|office|stores|store)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:operates?\s+(?:in|from)\s+)?(\d+)\s+(?:cities|locations|markets?)",
        re.IGNORECASE,
    ),
]

INDUSTRY_KEYWORDS = {
    "Manufacturing": [
        "manufacturer",
        "manufacturing",
        "factory",
        "industrial",
        "production",
    ],
    "Retail": ["retail", "ecommerce", "store", "shop"],
    "Logistics": ["logistics", "warehouse", "supply chain", "freight", "transport"],
    "Healthcare": ["healthcare", "medical", "hospital", "pharma", "pharmaceutical"],
    "Technology": ["software", "saas", "technology", "it services", "digital", "tech"],
    "Furniture": ["furniture", "interior", "home decor"],
    "Food & Beverage": ["food", "beverage", "biscuits", "snacks", "bakery", "oil"],
    "Mining": ["mica", "mining", "minerals"],
    "Education": ["education", "school", "college", "university", "training"],
    "Finance": ["finance", "banking", "insurance", "investment"],
    "Real Estate": ["real estate", "property", "construction", "building"],
    "Automotive": ["automotive", "vehicle", "car", "transportation"],
    "Agriculture": ["agriculture", "farming", "organic", "seeds"],
    "Chemicals": ["chemical", "chemicals", "solvents", "polymers"],
    "Textiles": ["textile", "textiles", "fabric", "yarn", "garments"],
    "Oil & Gas": ["oil", "gas", "petroleum", "lubricant", "fuel"],
}


def _extract_first(patterns: List[re.Pattern[str]], text: str) -> str:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return " ".join(match.group(1).split())
    return ""


def _extract_employee_count(text: str) -> str:
    extracted = extract_emp_count(text)
    return extracted if extracted else ""


def _extract_turnover(text: str) -> str:
    extracted = extract_turn(text)
    return extracted if extracted else ""


def _extract_branch_count(text: str) -> str:
    extracted = _extract_first(BRANCH_PATTERNS, text)
    return extracted if extracted else ""


def _extract_contact_name(text: str) -> str:
    name_patterns = [
        r"(?:ceo|chief executive)\s*(?:officer)?[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"(?:director|md|managing director)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"(?:founder|proprietor|owner)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
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

    if not enriched.get("employee_count"):
        enriched["employee_count"] = _extract_employee_count(combined_text)

    if not enriched.get("turnover"):
        enriched["turnover"] = _extract_turnover(combined_text)

    if not enriched.get("branch_count"):
        enriched["branch_count"] = _extract_branch_count(combined_text)

    if not enriched.get("contact_name"):
        enriched["contact_name"] = _extract_contact_name(combined_text)

    erp_from_text = extract_erp_from_text(combined_text)
    if erp_from_text:
        enriched["erp_software"] = erp_from_text
    elif detect_erp_name(combined_text):
        enriched["erp_software"] = detect_erp_name(combined_text)

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
    enriched.setdefault("employee_count", "")
    enriched.setdefault("branch_count", "")
    enriched.setdefault("turnover", "")
    enriched.setdefault("contact_name", "")
    enriched.setdefault("erp_software", "")

    return enriched
