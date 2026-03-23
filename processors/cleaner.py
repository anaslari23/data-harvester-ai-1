from __future__ import annotations

import re
from typing import Any, Dict
from urllib.parse import urlparse


from extractors.email_extractor import is_valid_email
from extractors.phone_extractor import is_valid_phone


TEXT_KEYS = {
    "company_name",
    "website",
    "phone",
    "email",
    "address",
    "city",
    "state",
    "country",
    "industry",
    "industry_type",
    "description",
    "additional_info",
    "source",
}


def _clean_text(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", value)
    return value


def _valid_url(url: str) -> bool:
    if not url:
        return False
    if url.startswith(("http://", "https://")):
        parsed = urlparse(url)
        return bool(parsed.netloc and "." in parsed.netloc)
    return False


def _valid_email(email: str) -> bool:
    return is_valid_email(email)


def _valid_phone(phone: str) -> bool:
    return is_valid_phone(phone)


def _valid_company_name(name: str) -> bool:
    if not name:
        return False
    name_lower = name.lower()
    invalid_patterns = [
        "undefined",
        "null",
        "none",
        "test company",
        "sample company",
        "click here",
        "read more",
        "learn more",
    ]
    if any(pattern in name_lower for pattern in invalid_patterns):
        return False
    if len(name.strip()) < 2:
        return False
    return True


def clean_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for key, value in rec.items():
        if isinstance(value, str):
            text = _clean_text(value)
            cleaned[key] = text if text else ""
        else:
            cleaned[key] = value if value is not None else ""

    email = str(cleaned.get("email", "")).strip()
    if email and not _valid_email(email):
        cleaned["email"] = ""

    phone = str(cleaned.get("phone", "")).strip()
    if phone and not _valid_phone(phone):
        cleaned["phone"] = ""

    website = str(cleaned.get("website", "")).strip()
    if website and not _valid_url(website):
        cleaned["website"] = ""

    company_name = str(cleaned.get("company_name", "")).strip()
    if company_name and not _valid_company_name(company_name):
        cleaned["company_name"] = ""

    for key in TEXT_KEYS:
        cleaned.setdefault(key, "")

    return cleaned
