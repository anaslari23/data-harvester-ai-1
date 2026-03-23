from __future__ import annotations

import html
import re
from typing import Any, Dict, List
from urllib.parse import urlparse


from extractors.email_extractor import is_valid_email, is_business_email
from extractors.phone_extractor import is_valid_phone, normalize_phone
from extractors.company_extractor import is_valid_company_name, _score_company_name


HTML_TAG_REGEX = re.compile(r"<[^>]+>")
HTML_ENTITY_REGEX = re.compile(r"&[a-zA-Z]+;|&#\d+;")
EXTRA_WHITESPACE_REGEX = re.compile(r"\s+")
NON_PRINTABLE_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


LIKELY_GARBLED_PATTERNS = [
    r"[\u0000-\u001f\u007f-\u009f]",
    r"[\xc0-\xff]{3,}",
    r"[\ufffc-\uffff]",
]

GARBLED_REGEX = re.compile("|".join(LIKELY_GARBLED_PATTERNS), re.UNICODE)

LIKELY_LOREM = [
    "lorem ipsum",
    "dolor sit amet",
    "consectetur adipiscing elit",
    "sed do eiusmod",
    "tempor incididunt",
    "labore et dolore magna",
]

SUSPICIOUS_URL_CHARS = ["{", "}", "\\", "^", "`", "~", "[", "]", "|"]


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


def has_garbled_text(text: str) -> bool:
    if not text:
        return False
    if GARBLED_REGEX.search(text):
        return True
    non_ascii = sum(1 for c in text if ord(c) > 127)
    if non_ascii > len(text) * 0.3 and non_ascii > 10:
        return True
    return False


def is_valid_url(url: str) -> bool:
    if not url:
        return False
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    try:
        parsed = urlparse(url)
        if not parsed.netloc or "." not in parsed.netloc:
            return False
        if len(parsed.netloc) < 5:
            return False
        if any(c in url for c in SUSPICIOUS_URL_CHARS):
            return False
        if parsed.netloc.count(".") < 1:
            return False
        return True
    except Exception:
        return False


def is_valid_description(desc: str) -> bool:
    if not desc:
        return True
    desc_lower = desc.lower()
    if len(desc) < 30:
        return False
    if desc_lower in ["n/a", "na", "none", "null", "-", ".", "n/a.", "..."]:
        return False
    if any(p in desc_lower for p in LIKELY_LOREM):
        return False
    if has_garbled_text(desc):
        return False
    return True


def is_meaningful_text(text: str) -> bool:
    if not text or len(text) < 5:
        return False
    words = text.split()
    if len(words) < 2:
        return False
    letters = re.sub(r"[^a-zA-Z]", "", text)
    if len(letters) < len(text) * 0.5:
        return False
    return True


def calculate_data_quality_score(
    record: Dict[str, Any], website_domain: str = ""
) -> float:
    score = 0.0
    fields_with_data = 0
    total_fields = 10

    company_name = record.get("company_name", "")
    if company_name:
        company_score = _score_company_name(company_name, website_domain)
        if company_score >= 4:
            score += 3.0
            fields_with_data += 1
        elif company_score >= 3:
            score += 2.0
            fields_with_data += 1

    website = record.get("website", "")
    if website:
        score += 1.5
        fields_with_data += 1

    email = record.get("email", "")
    if email:
        email_score = 2.0 if is_business_email(email, website_domain) else 1.5
        score += email_score
        fields_with_data += 1

    phone = record.get("phone", "")
    if phone:
        score += 1.5
        fields_with_data += 1

    address = record.get("address", "")
    city = record.get("city", "")
    state = record.get("state", "")
    if address or city or state:
        score += 1.0
        fields_with_data += 1
        if city:
            score += 0.5
        if state:
            score += 0.3

    industry = record.get("industry", "") or record.get("industry_type", "")
    if industry and is_meaningful_text(industry):
        score += 0.5
        fields_with_data += 1

    description = record.get("description", "")
    if description and len(description) > 50 and is_meaningful_text(description):
        score += 1.0
        fields_with_data += 1
    elif description and len(description) > 20:
        score += 0.3

    completeness_bonus = (fields_with_data / total_fields) * 2.0
    score += completeness_bonus

    return round(score, 2)


MINIMUM_QUALITY_THRESHOLD = 5.5


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

    website = cleaned.get("website", "")
    website_domain = ""
    if website and is_valid_url(website):
        try:
            website_domain = urlparse(website).netloc
        except Exception:
            pass

    company_name = clean_text(cleaned.get("company_name", ""))
    if company_name and is_valid_company_name(company_name, website_domain):
        cleaned["company_name"] = company_name
    else:
        cleaned["company_name"] = ""

    email = clean_text(cleaned.get("email", ""))
    if email:
        if is_business_email(email, website_domain):
            cleaned["email"] = email.lower()
        elif is_valid_email(email):
            cleaned["email"] = email.lower()
        else:
            cleaned["email"] = ""
    else:
        cleaned["email"] = ""

    phone = clean_text(cleaned.get("phone", ""))
    if phone and is_valid_phone(phone):
        cleaned["phone"] = normalize_phone(phone)
    else:
        cleaned["phone"] = ""

    if website and is_valid_url(website):
        cleaned["website"] = website.lower()
    else:
        cleaned["website"] = ""

    description = clean_text(cleaned.get("description", ""))
    if description:
        if has_garbled_text(description):
            cleaned["description"] = ""
        elif is_valid_description(description):
            cleaned["description"] = description[:1000]
        else:
            cleaned["description"] = ""
    else:
        cleaned["description"] = ""

    address = clean_text(cleaned.get("address", ""))
    if address and is_meaningful_text(address):
        cleaned["address"] = address[:500]
    else:
        cleaned["address"] = ""

    for field in TEXT_FIELDS:
        cleaned.setdefault(field, "")

    return cleaned


def filter_by_quality(
    records: List[Dict[str, Any]], threshold: float = MINIMUM_QUALITY_THRESHOLD
) -> List[Dict[str, Any]]:
    qualified = []
    for record in records:
        score = calculate_data_quality_score(record, record.get("website", ""))
        if score >= threshold:
            qualified.append(record)
    return qualified


def clean_and_filter(
    raw_records: List[Dict[str, Any]],
    quality_threshold: float = MINIMUM_QUALITY_THRESHOLD,
) -> List[Dict[str, Any]]:
    cleaned = [clean_record(r) for r in raw_records]
    return filter_by_quality(cleaned, threshold=quality_threshold)
