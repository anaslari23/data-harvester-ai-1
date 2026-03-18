from __future__ import annotations

import html
import re
from typing import Any, Dict
from urllib.parse import urlparse


EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_REGEX = re.compile(r"(\+?\d[\d \-]{8,}\d)")
HTML_TAG_REGEX = re.compile(r"<[^>]+>")
HTML_ENTITY_REGEX = re.compile(r"&[a-zA-Z]+;|&#\d+;")
EXTRA_WHITESPACE_REGEX = re.compile(r"\s+")
SPECIAL_CHARS_REGEX = re.compile(r"[\x00-\x1f\x7f-\x9f]")
NON_PRINTABLE_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


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

GENERIC_EMAILS = {"noreply@", "no-reply@", "donotreply@", "hello@", "privacy@"}


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = HTML_TAG_REGEX.sub(" ", text)
    text = HTML_ENTITY_REGEX.sub(lambda m: html.unescape(m.group(0)), text)
    return text


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = strip_html(text)
    text = html.unescape(text)
    text = NON_PRINTABLE_REGEX.sub("", text)
    text = EXTRA_WHITESPACE_REGEX.sub(" ", text)
    return text.strip()


def is_valid_url(url: str) -> bool:
    if not url:
        return False
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc and "." in parsed.netloc and len(parsed.netloc) > 4)
    except Exception:
        return False


def is_valid_email(email: str) -> bool:
    if not email:
        return False
    email_lower = email.lower().strip()
    domain = email_lower.split("@")[-1] if "@" in email_lower else ""
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return False
    if any(email_lower.startswith(gen) for gen in GENERIC_EMAILS):
        return False
    return bool(EMAIL_REGEX.fullmatch(email_lower))


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return 10 <= len(digits) <= 15


def is_valid_company_name(name: str) -> bool:
    if not name:
        return False
    name_lower = name.lower().strip()
    invalid_patterns = [
        "undefined",
        "null",
        "none",
        "test company",
        "sample company",
        "click here",
        "read more",
        "learn more",
        "http",
        "www.",
        "example.com",
        "example.org",
        "localhost",
    ]
    if any(pattern in name_lower for pattern in invalid_patterns):
        return False
    if len(name.strip()) < 2:
        return False
    if any(char in name for char in ["<", ">", "{", "}", "[", "]"]):
        return False
    return True


def is_valid_description(desc: str) -> bool:
    if not desc:
        return True
    desc_lower = desc.lower()
    if len(desc) < 10:
        return False
    if desc_lower in ["n/a", "na", "none", "null", "-", "."]:
        return False
    lorem_patterns = ["lorem ipsum", "dolor sit amet", " consectetur ", " adipiscing "]
    if any(p in desc_lower for p in lorem_patterns):
        return False
    return True


def calculate_data_quality_score(record: Dict[str, Any]) -> float:
    score = 0.0
    fields_with_data = 0
    total_fields = 10

    if record.get("company_name"):
        score += 2.0
        fields_with_data += 1
    if record.get("website"):
        score += 1.5
        fields_with_data += 1
    if record.get("email"):
        score += 2.0
        fields_with_data += 1
    if record.get("phone"):
        score += 1.5
        fields_with_data += 1
    if record.get("address"):
        score += 1.0
        fields_with_data += 1
    if record.get("city"):
        score += 0.5
        fields_with_data += 1
    if record.get("state"):
        score += 0.5
        fields_with_data += 1
    if record.get("industry"):
        score += 0.5
        fields_with_data += 1
    if record.get("description") and len(record.get("description", "")) > 20:
        score += 0.5
        fields_with_data += 1

    completeness_bonus = (fields_with_data / total_fields) * 1.0
    score += completeness_bonus

    return score


MINIMUM_QUALITY_THRESHOLD = 3.5


TEXT_FIELDS = {
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


def clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = {}

    for key, value in record.items():
        if isinstance(value, str):
            cleaned[key] = clean_text(value)
        else:
            cleaned[key] = value if value is not None else ""

    cleaned["company_name"] = clean_text(cleaned.get("company_name", ""))
    if not is_valid_company_name(cleaned["company_name"]):
        cleaned["company_name"] = ""

    email = clean_text(cleaned.get("email", ""))
    if email and not is_valid_email(email):
        cleaned["email"] = ""

    phone = clean_text(cleaned.get("phone", ""))
    if phone and not is_valid_phone(phone):
        cleaned["phone"] = ""

    website = clean_text(cleaned.get("website", ""))
    if website and not is_valid_url(website):
        cleaned["website"] = ""

    description = clean_text(cleaned.get("description", ""))
    if not is_valid_description(description):
        cleaned["description"] = ""

    for field in TEXT_FIELDS:
        cleaned.setdefault(field, "")

    return cleaned


def filter_by_quality(records: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    qualified = []
    for record in records:
        score = calculate_data_quality_score(record)
        if score >= MINIMUM_QUALITY_THRESHOLD:
            qualified.append(record)
    return qualified


def clean_and_filter(raw_records: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    cleaned = [clean_record(r) for r in raw_records]
    return filter_by_quality(cleaned)
