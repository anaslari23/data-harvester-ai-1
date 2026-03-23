from __future__ import annotations

import json
import re
from typing import Optional
from bs4 import BeautifulSoup


NOISE_SUFFIXES = [
    r"\s*[-|–—]\s*.+$",
    r"\s*::\s*.+$",
    r"\s*»\s*.+$",
    r"\bHome\b.*$",
    r"\bWelcome\b.*$",
    r"\bOfficial\b.*$",
]

COMPANY_SUFFIXES = [
    "Private Limited",
    "Pvt Ltd",
    "Pvt. Ltd.",
    "Pvt. Ltd",
    "Limited",
    "Ltd.",
    "Ltd",
    "LLP",
    "Inc.",
    "Inc",
    "Corporation",
    "Corp.",
    "& Co.",
    "and Co.",
]


def extract_company_name(soup: BeautifulSoup, url: str = "") -> Optional[str]:
    """Extract company name with confidence scoring."""
    candidates = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") in (
                    "Organization",
                    "LocalBusiness",
                    "Corporation",
                ):
                    name = item.get("name", "").strip()
                    if name and 2 < len(name) < 80:
                        candidates.append((name, 10))
        except Exception:
            pass

    tag = soup.find("meta", property="og:site_name")
    if tag and tag.get("content"):
        candidates.append((tag["content"].strip(), 9))

    text = soup.get_text(separator=" ")
    cp = re.search(
        r"©\s*(?:\d{4})?\s*([A-Z][A-Za-z0-9\s&.,()-]{2,60}?)"
        r"(?:Pvt|Ltd|Private|All Rights|\.)",
        text,
    )
    if cp:
        candidates.append((cp.group(1).strip(), 8))

    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)
        for pattern in NOISE_SUFFIXES:
            title = re.sub(pattern, "", title, flags=re.I).strip()
        if 2 < len(title) < 80:
            candidates.append((title, 6))

    h1 = soup.find("h1")
    if h1:
        h1_text = h1.get_text(strip=True)
        word_count = len(h1_text.split())
        if 1 <= word_count <= 5 and len(h1_text) < 60:
            candidates.append((h1_text, 5))

    if not candidates:
        return None

    best = max(candidates, key=lambda x: x[1])[0]

    best = re.sub(
        r"\b(Home|Welcome|Index|Official|Website|Online|Portal)\b", "", best, flags=re.I
    ).strip(" -|:")

    if re.search(r"[A-Za-z]{2,}", best):
        return best
    return None


def extract_employee_count(text: str) -> Optional[str]:
    """Extract employee count with strict validation."""
    patterns = [
        r"(\d[\d,]*)\s*\+?\s*employees",
        r"team\s+of\s+(?:over\s+)?(\d[\d,]*)",
        r"workforce\s+of\s+(?:over\s+)?(\d[\d,]*)",
        r"(\d[\d,]*)\s*\+?\s*professionals",
        r"over\s+(\d[\d,]*)\s+(?:people|staff|employees)",
        r"(\d[\d,]*)\s*[-–]\s*strong\s+team",
        r"employs?\s+(?:over\s+)?(\d[\d,]*)",
        r"(\d[\d,]*)\s*\+?\s*(?:member|associate|colleague)s?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                n = int(raw)
                if not (1 <= n <= 500000):
                    continue
                if n <= 10:
                    return "1-10"
                if n <= 50:
                    return "11-50"
                if n <= 200:
                    return "51-200"
                if n <= 500:
                    return "201-500"
                if n <= 1000:
                    return "501-1000"
                return "1000+"
            except ValueError:
                continue
    return None


def extract_turnover(text: str) -> Optional[str]:
    """Extract turnover from text."""
    patterns = [
        r"(?:annual\s+)?(?:turnover|revenue|sales)\s*:?\s*"
        r"(?:Rs\.?|₹|INR)?\s*([\d,.]+)\s*(crore|cr|lakh|million|billion)",
        r"(?:Rs\.?|₹)\s*([\d,.]+)\s*(cr(?:ore)?)",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m and len(m.groups()) >= 2:
            return f"₹{m.group(1)} {m.group(2).title()}"
        elif m:
            return f"₹{m.group(1)}"
    return None


def extract_erp_from_text(text: str) -> Optional[str]:
    """Detect ERP from page text."""
    erp_patterns = {
        "SAP": r"\bSAP\b",
        "Oracle": r"\bOracle\b",
        "Tally": r"\bTally(?:Prime|ERP)?\b",
        "Zoho": r"\bZoho\s*(?:Books|CRM|ERP)?\b",
        "Odoo": r"\bOdoo\b",
        "Infor": r"\bInfor\b",
        "Microsoft Dynamics": r"\bDynamics\s*365\b|\bDynamics\s*AX\b",
        "Busy": r"\bBUSY\s*(?:Software|Accounting)?\b",
        "Marg ERP": r"\bMARG\s*ERP\b",
    }

    text_upper = text.upper()
    matches = []
    for erp, pattern in erp_patterns.items():
        if re.search(pattern, text_upper, re.I):
            matches.append(erp)

    return matches[0] if matches else None
