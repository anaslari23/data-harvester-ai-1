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
        "fabricat",
    ],
    "Retail": ["retail", "ecommerce", "e-commerce", "store", "shop", "wholesaler", "wholesale"],
    "Logistics": ["logistics", "warehouse", "supply chain", "freight", "transport", "shipping", "courier"],
    "Healthcare": ["healthcare", "medical", "hospital", "pharma", "pharmaceutical", "clinic", "health"],
    "Technology": ["software", "saas", "technology", "it services", "digital", "tech", "cyber", "cloud", "ai ", "data"],
    "Furniture": ["furniture", "interior", "home decor", "furnishing"],
    "Food & Beverage": ["food", "beverage", "biscuits", "snacks", "bakery", "oil", "dairy", "agro"],
    "Mining": ["mica", "mining", "minerals", "quarry"],
    "Education": ["education", "school", "college", "university", "training", "institute", "academy"],
    "Finance": ["finance", "banking", "insurance", "investment", "nbfc", "fintech"],
    "Real Estate": ["real estate", "property", "construction", "building", "infra", "developer"],
    "Automotive": ["automotive", "vehicle", "car", "transportation", "auto parts", "tyre"],
    "Agriculture": ["agriculture", "farming", "organic", "seeds", "agri", "horticulture"],
    "Chemicals": ["chemical", "chemicals", "solvents", "polymers", "dyes", "pigment"],
    "Textiles": ["textile", "textiles", "fabric", "yarn", "garments", "apparel", "weaving"],
    "Oil & Gas": ["oil", "gas", "petroleum", "lubricant", "fuel", "refinery"],
    "Toys & Games": ["toy", "toys", "games", "game", "play", "hobby"],
    "Packaging": ["packaging", "packing", "corrugated", "carton", "box", "container"],
    "Steel & Metal": ["steel", "metal", "iron", "aluminium", "alloy", "casting", "forging"],
    "Plastics & Rubber": ["plastic", "rubber", "polymer", "pvc", "polyester"],
    "Electronics": ["electronics", "electrical", "semiconductor", "pcb", "circuit", "component"],
}

# Expanded role patterns — covers Owner, IT Head, Finance Head, CEO, Director, etc.
_CONTACT_PATTERNS = [
    # CEO / Chief Executive
    re.compile(
        r"(?:ceo|chief\s+executive(?:\s+officer)?)\s*[:\-–]\s*"
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Er\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        re.IGNORECASE,
    ),
    # Managing Director / MD
    re.compile(
        r"(?:managing\s+director|m\.?d\.?)\s*[:\-–]\s*"
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        re.IGNORECASE,
    ),
    # Director
    re.compile(
        r"\bdirector\s*[:\-–]\s*"
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        re.IGNORECASE,
    ),
    # Owner / Proprietor
    re.compile(
        r"(?:owner|proprietor)\s*[:\-–]\s*"
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        re.IGNORECASE,
    ),
    # Founder / Co-Founder
    re.compile(
        r"(?:co-?founder|founder)\s*[:\-–]\s*"
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        re.IGNORECASE,
    ),
    # IT Head / Head of IT / CTO / Chief Technology Officer
    re.compile(
        r"(?:it\s+head|head\s+of\s+it|cto|chief\s+technology(?:\s+officer)?|it\s+director|technical\s+director)\s*[:\-–]\s*"
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        re.IGNORECASE,
    ),
    # Finance Head / CFO / Chief Financial Officer
    re.compile(
        r"(?:finance\s+head|head\s+of\s+finance|cfo|chief\s+financial(?:\s+officer)?|finance\s+director)\s*[:\-–]\s*"
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        re.IGNORECASE,
    ),
    # COO / Chief Operating Officer
    re.compile(
        r"(?:coo|chief\s+operating(?:\s+officer)?|operations\s+director)\s*[:\-–]\s*"
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        re.IGNORECASE,
    ),
    # Contact Person (common on IndiaMart / TradeIndia)
    re.compile(
        r"contact\s+(?:person|name)\s*[:\-–]?\s*"
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        re.IGNORECASE,
    ),
    # Name: / Key Person: — generic fallback
    re.compile(
        r"(?:key\s+person|authorised\s+signatory|partner)\s*[:\-–]\s*"
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        re.IGNORECASE,
    ),
]


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
    for pattern in _CONTACT_PATTERNS:
        match = pattern.search(text)
        if match:
            name = match.group(1).strip()
            # Basic sanity: at least two words and no obvious noise
            if len(name.split()) >= 1 and len(name) <= 60:
                return name
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
