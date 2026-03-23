from __future__ import annotations

import re
from typing import List, Optional, Set


INDIAN_MOBILE_REGEX = re.compile(r"(?:\+91[\s\-]?)?([6-9]\d{9})")
INDIAN_LANDLINE_REGEX = re.compile(
    r"(?:[\+]?91[\s\-]?)?(?:0?[\s\-]?)?(\d{2,5})[\s\-]?\d{6,8}"
)
US_PHONE_REGEX = re.compile(
    r"(?:\+?1[\s\-.]?)?(?:\(?\d{3}\)?[\s\-.]?)?\d{3}[\s\-.]?\d{4}"
)
UK_PHONE_REGEX = re.compile(r"(?:\+?44[\s\-.]?)?(?:0[\s\-.]?)?\d{4}[\s\-.]?\d{6}")
GENERIC_INTL_REGEX = re.compile(
    r"(?:\+?\d{1,4}[\s\-.]?)?\(?\d{1,4}\)?[\s\-.]?\d{1,4}[\s\-.]?\d{1,9}"
)

COMMON_SUSPICIOUS = [
    "0000000000",
    "1111111111",
    "2222222222",
    "3333333333",
    "4444444444",
    "5555555555",
    "6666666666",
    "7777777777",
    "8888888888",
    "9999999999",
    "1234567890",
    "0123456789",
    "9876543210",
    "0987654321",
    "1111111111111",
    "0000000000000",
]


def _extract_digits(phone: str) -> str:
    return re.sub(r"\D", "", phone)


def _is_repeating_number(digits: str, min_repeat: int = 6) -> bool:
    if len(digits) < min_repeat:
        return False
    if digits in COMMON_SUSPICIOUS:
        return True
    first_char = digits[0]
    if all(c == first_char for c in digits):
        return True
    return False


def _is_sequential_number(digits: str) -> bool:
    if len(digits) < 8:
        return False
    ascending = "0123456789"
    descending = "9876543210"
    if digits in ascending or digits in descending:
        return True
    return False


def _is_valid_length(digits: str) -> bool:
    length = len(digits)
    if length < 10 or length > 15:
        return False
    return True


def _looks_like_year(digits: str) -> bool:
    years = [str(y) for y in range(1900, 2030)]
    return digits in years


def _looks_like_date(digits: str) -> bool:
    if len(digits) == 4:
        month = int(digits[:2])
        day = int(digits[2:])
        if 1 <= month <= 12 and 1 <= day <= 31:
            return True
    return False


def is_valid_phone(phone: str, region_hint: Optional[str] = None) -> bool:
    if not phone:
        return False

    phone = phone.strip()
    digits = _extract_digits(phone)

    if not _is_valid_length(digits):
        return False

    if _is_repeating_number(digits):
        return False

    if _is_sequential_number(digits):
        return False

    if _looks_like_year(digits):
        return False

    if _looks_like_date(digits):
        return False

    if digits.startswith("0") * 10 == len(digits):
        return False

    if region_hint:
        if region_hint.lower() in ["india", "in"]:
            return _validate_indian_phone(digits)
        elif region_hint.lower() in ["usa", "us", "canada", "ca"]:
            return _validate_us_phone(digits)
        elif region_hint.lower() in ["uk", "gb"]:
            return _validate_uk_phone(digits)

    return True


def _validate_indian_phone(digits: str) -> bool:
    if len(digits) == 10:
        if digits[0] in "6789":
            return True
    if len(digits) == 11 and digits.startswith("0"):
        return digits[1] in "6789"
    if len(digits) == 12 and digits.startswith("91"):
        return digits[2] in "6789"
    if len(digits) == 13 and digits.startswith("+91"):
        return digits[3] in "6789"
    return False


def _validate_us_phone(digits: str) -> bool:
    if len(digits) == 10:
        if digits[0] not in "012":
            return True
    if len(digits) == 11 and digits.startswith("1"):
        if digits[1] not in "012":
            return True
    return False


def _validate_uk_phone(digits: str) -> bool:
    if len(digits) == 10:
        return True
    if len(digits) == 11 and digits.startswith("0"):
        return True
    if len(digits) == 12 and digits.startswith("44"):
        return True
    return False


def normalize_phone(phone: str, region_hint: Optional[str] = None) -> str:
    if not phone:
        return ""

    digits = _extract_digits(phone)

    if not is_valid_phone(phone, region_hint):
        return ""

    if region_hint and region_hint.lower() in ["india", "in"]:
        if len(digits) == 10:
            return f"+91{digits}"
        elif len(digits) == 11 and digits.startswith("0"):
            return f"+91{digits[1:]}"
        elif len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"

    if len(digits) >= 10:
        return f"+{digits}"

    return digits


def extract_phones(
    text: str, max_phones: int = 5, region_hint: Optional[str] = None
) -> List[str]:
    if not text:
        return []

    all_matches: Set[str] = set()

    for regex in [
        INDIAN_MOBILE_REGEX,
        INDIAN_LANDLINE_REGEX,
        US_PHONE_REGEX,
        UK_PHONE_REGEX,
        GENERIC_INTL_REGEX,
    ]:
        for match in regex.finditer(text):
            phone = match.group(0).strip()
            if phone:
                all_matches.add(phone)

    valid_phones: List[str] = []
    for phone in all_matches:
        normalized = normalize_phone(phone, region_hint)
        if normalized and is_valid_phone(phone, region_hint):
            if normalized not in valid_phones:
                valid_phones.append(normalized)

    return valid_phones[:max_phones]


def extract_best_phone(text: str, region_hint: Optional[str] = None) -> str:
    phones = extract_phones(text, max_phones=1, region_hint=region_hint)
    return phones[0] if phones else ""
