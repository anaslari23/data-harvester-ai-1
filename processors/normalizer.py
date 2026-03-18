from __future__ import annotations

import re
from typing import Any, Dict
from urllib.parse import urlparse


NON_DIGIT_PHONE = re.compile(r"[^\d+]")
WHITESPACE = re.compile(r"\s+")
EXTRA_CHARS = re.compile(r"[\(\)\-\.\[\]]")

INDUSTRY_NORMALIZATIONS = {
    "it services": "IT Services",
    "it service": "IT Services",
    "information technology": "IT Services",
    "software": "Software",
    "software development": "Software Development",
    "software services": "Software Services",
    "manufacturing": "Manufacturing",
    "retail": "Retail",
    "ecommerce": "E-Commerce",
    "e-commerce": "E-Commerce",
    "logistics": "Logistics",
    "transportation": "Transportation",
    "healthcare": "Healthcare",
    "education": "Education",
    "finance": "Finance",
    "banking": "Banking",
    "insurance": "Insurance",
    "real estate": "Real Estate",
    "construction": "Construction",
    "automotive": "Automotive",
    "food & beverage": "Food & Beverage",
    "food and beverage": "Food & Beverage",
    "telecommunications": "Telecommunications",
    "media": "Media",
    "entertainment": "Entertainment",
    "hospitality": "Hospitality",
    "energy": "Energy",
    "mining": "Mining",
    "agriculture": "Agriculture",
    "pharmaceuticals": "Pharmaceuticals",
    "textiles": "Textiles",
    "chemicals": "Chemicals",
    "machinery": "Machinery",
    "electronics": "Electronics",
}


def normalize_phone(phone: str | None) -> str:
    if not phone:
        return ""
    normalized = NON_DIGIT_PHONE.sub("", phone)
    normalized = EXTRA_CHARS.sub("", normalized)
    normalized = WHITESPACE.sub("", normalized)
    if normalized.startswith("91") and len(normalized) > 10:
        normalized = "+" + normalized
    elif normalized.startswith("0") and len(normalized) == 11:
        normalized = "+91" + normalized[1:]
    return normalized


def normalize_url(url: str | None) -> str:
    if not url:
        return ""
    value = url.strip()
    if not value:
        return ""
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    parsed = urlparse(value)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/")
    if parsed.query:
        return f"{parsed.scheme.lower()}://{host}{path}?{parsed.query}"
    return f"{parsed.scheme.lower()}://{host}{path}"


def normalize_email(email: str | None) -> str:
    if not email:
        return ""
    return email.strip().lower()


def normalize_industry(industry: str) -> str:
    if not industry:
        return ""
    normalized = industry.strip().lower()
    if normalized in INDUSTRY_NORMALIZATIONS:
        return INDUSTRY_NORMALIZATIONS[normalized]
    return industry.strip().title()


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return WHITESPACE.sub(" ", text.strip())


def normalize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(rec)
    normalized["company_name"] = normalize_text(normalized.get("company_name", ""))
    normalized["website"] = normalize_url(normalized.get("website", ""))
    normalized["phone"] = normalize_phone(normalized.get("phone", ""))
    normalized["email"] = normalize_email(normalized.get("email", ""))
    normalized["industry"] = normalize_industry(normalized.get("industry", ""))
    normalized["industry_type"] = normalize_industry(
        normalized.get("industry_type", "")
    )
    normalized["address"] = normalize_text(normalized.get("address", ""))
    normalized["city"] = normalize_text(normalized.get("city", "")).title()
    normalized["state"] = normalize_text(normalized.get("state", "")).title()
    normalized["country"] = normalize_text(normalized.get("country", "")).title()
    normalized["description"] = normalize_text(normalized.get("description", ""))
    normalized["additional_info"] = normalize_text(
        normalized.get("additional_info", "")
    )
    normalized["source"] = normalize_text(normalized.get("source", ""))
    return normalized


def normalize_url(url: str | None) -> str:
    if not url:
        return ""
    value = url.strip()
    if not value:
        return ""
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    parsed = urlparse(value)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/")
    if parsed.query:
        return f"{parsed.scheme.lower()}://{host}{path}?{parsed.query}"
    return f"{parsed.scheme.lower()}://{host}{path}"


def normalize_email(email: str | None) -> str:
    if not email:
        return ""
    return email.strip().lower()


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return WHITESPACE.sub(" ", text.strip())


def normalize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(rec)
    normalized["company_name"] = normalize_text(normalized.get("company_name", ""))
    normalized["website"] = normalize_url(normalized.get("website", ""))
    normalized["phone"] = normalize_phone(normalized.get("phone", ""))
    normalized["email"] = normalize_email(normalized.get("email", ""))
    normalized["industry"] = normalize_text(normalized.get("industry", "")).title()
    normalized["industry_type"] = normalize_text(
        normalized.get("industry_type", "")
    ).title()
    normalized["address"] = normalize_text(normalized.get("address", ""))
    normalized["city"] = normalize_text(normalized.get("city", "")).title()
    normalized["state"] = normalize_text(normalized.get("state", "")).title()
    normalized["country"] = normalize_text(normalized.get("country", "")).title()
    normalized["description"] = normalize_text(normalized.get("description", ""))
    normalized["additional_info"] = normalize_text(
        normalized.get("additional_info", "")
    )
    normalized["source"] = normalize_text(normalized.get("source", ""))
    return normalized
