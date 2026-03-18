from __future__ import annotations

import re
from typing import Any, Dict
from urllib.parse import urlparse

from extractors.email_extractor import EMAIL_REGEX
from extractors.phone_extractor import PHONE_REGEX


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

DISPOSABLE_EMAIL_DOMAINS = {
    "tempmail.com",
    "guerrillamail.com",
    "mailinator.com",
    "throwaway.com",
    "fakeinbox.com",
    "10minutemail.com",
    "temp-mail.org",
    "yopmail.com",
    "trashmail.com",
    "dispostable.com",
    "maildrop.cc",
    "getairmail.com",
    "mailnesia.com",
    "spamgourmet.com",
    "mintemail.com",
    "sharklasers.com",
    "guerrillamailblock.com",
    "pokemail.net",
    "spambox.us",
}

GENERIC_EMAILS = {
    "noreply@",
    "no-reply@",
    "donotreply@",
    "hello@",
    "privacy@",
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
    if not email:
        return False
    email_lower = email.lower()
    domain = email_lower.split("@")[-1] if "@" in email_lower else ""
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return False
    if any(email_lower.startswith(gen) for gen in GENERIC_EMAILS):
        return False
    return bool(EMAIL_REGEX.fullmatch(email_lower))


def _valid_phone(phone: str) -> bool:
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 10:
        return False
    if len(digits) > 15:
        return False
    return True


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
