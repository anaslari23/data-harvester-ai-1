from __future__ import annotations

import re
from typing import List, Optional, Set


EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
VALID_TLDS = {
    "com",
    "org",
    "net",
    "edu",
    "gov",
    "co",
    "uk",
    "io",
    "ai",
    "io",
    "app",
    "dev",
    "info",
    "biz",
    "pro",
    "me",
    "us",
    "ca",
    "au",
    "de",
    "fr",
    "jp",
    "cn",
    "in",
    "nl",
    "es",
    "it",
    "br",
    "mx",
    "ru",
    "ch",
    "at",
    "be",
    "se",
    "no",
    "dk",
    "fi",
    "pl",
    "pt",
    "ie",
    "nz",
    "sg",
    "hk",
    "kr",
    "za",
    "ae",
    "ph",
    "my",
    "th",
    "vn",
    "id",
    "eg",
    "pk",
    "bd",
    "lk",
    "np",
    "mm",
    "kh",
    "np",
    "lk",
    "ir",
    "iq",
    "sa",
    "qa",
    "kw",
    "bh",
    "om",
    "jo",
    "lb",
    "sy",
    "ps",
    "il",
    "tr",
    "ua",
    "by",
    "kz",
    "uz",
    "az",
    "ge",
    "am",
    "mn",
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
    "mailcatch.com",
    "spamex.com",
    "emailwarden.com",
    "throwawaymail.com",
    "tempinbox.com",
    "getnada.com",
    "mohmal.com",
    "guerrillamail.org",
    "guerrillamail.net",
    "guerrillamail.biz",
    "guerrillamail.de",
    "grr.la",
    "mailforspam.com",
}

GENERIC_EMAILS = {
    "noreply@",
    "no-reply@",
    "donotreply@",
    "noreply",
    "no-reply",
    "donotreply",
}


def _extract_domain(email: str) -> str:
    if "@" in email:
        return email.lower().split("@")[-1]
    return ""


def _has_valid_structure(email: str) -> bool:
    if not email or "@" not in email:
        return False
    parts = email.lower().split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain:
        return False
    if len(local) > 64 or len(domain) > 255:
        return False
    if ".." in local or local.startswith(".") or local.endswith("."):
        return False
    return True


def _has_valid_tld(domain: str) -> bool:
    if not domain or "." not in domain:
        return False
    tld = domain.rsplit(".", 1)[-1]
    return tld in VALID_TLDS and len(tld) >= 2


def _has_suspicious_patterns(email: str) -> bool:
    email_lower = email.lower()
    suspicious = [
        "example.com",
        "test.com",
        "localhost",
        "127.0.0.1",
        "domain.com",
        "sample.com",
        "dummy.com",
        "fake.com",
    ]
    if any(s in email_lower for s in suspicious):
        return True
    if re.search(r"[\u4e00-\u9fff\u0600-\u06ff\u0400-\u04ff]", email):
        return True
    if (
        re.search(r"[^\x00-\x7F]", email)
        and len(re.findall(r"[^\x00-\x7F]", email)) > 2
    ):
        return True
    return False


def is_valid_email(email: str, website_domain: Optional[str] = None) -> bool:
    if not email:
        return False

    email = email.strip().lower()

    if "@" not in email:
        return False

    if not _has_valid_structure(email):
        return False

    domain = _extract_domain(email)

    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return False

    if any(
        email.startswith(gen.replace("@", "")) or email.startswith(gen)
        for gen in GENERIC_EMAILS
    ):
        if not (
            website_domain
            and domain.replace("www.", "") == website_domain.replace("www.", "")
        ):
            pass

    if any(email.startswith(gen) for gen in GENERIC_EMAILS):
        return False

    if not _has_valid_tld(domain):
        return False

    if _has_suspicious_patterns(email):
        return False

    if not EMAIL_REGEX.fullmatch(email):
        return False

    return True


def is_business_email(email: str, website_domain: Optional[str] = None) -> bool:
    if not is_valid_email(email, website_domain):
        return False

    domain = _extract_domain(email)
    domain_base = domain.replace("www.", "").split(".")[0]

    generic_domains = {
        "gmail",
        "yahoo",
        "hotmail",
        "outlook",
        "aol",
        "icloud",
        "live",
        "msn",
        "ymail",
        "mail",
        "protonmail",
        "zoho",
        "rediffmail",
        "indiatimes",
        "sify",
        "eth.net",
    }

    if domain_base in generic_domains:
        return False

    return True


def extract_emails(
    text: str,
    website_domain: Optional[str] = None,
    max_emails: int = 5,
    prefer_business: bool = True,
) -> List[str]:
    if not text:
        return []

    matches = EMAIL_REGEX.findall(text)

    seen: Set[str] = set()
    business_emails: List[str] = []
    other_emails: List[str] = []

    for email in matches:
        email = email.strip().lower()

        if email in seen:
            continue
        seen.add(email)

        if is_business_email(email, website_domain):
            business_emails.append(email)
        elif is_valid_email(email):
            other_emails.append(email)

    if prefer_business and business_emails:
        return business_emails[:max_emails]

    all_valid = business_emails + other_emails
    return all_valid[:max_emails]


def extract_best_email(text: str, website_domain: Optional[str] = None) -> str:
    emails = extract_emails(text, website_domain, max_emails=1, prefer_business=True)
    return emails[0] if emails else ""
