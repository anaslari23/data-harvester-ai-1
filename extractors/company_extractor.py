from __future__ import annotations

import re
from typing import List, Optional, Tuple


COMPANY_SUFFIXES = {
    "private limited",
    "pvt ltd",
    "pvt. ltd.",
    "private ltd",
    "limited",
    "ltd",
    "ltd.",
    "llp",
    "inc",
    "inc.",
    "incorporated",
    "corporation",
    "corp",
    "corp.",
    "co",
    "co.",
    "company",
    "group",
    "holdings",
    "enterprises",
    "services",
    "solutions",
    "industries",
    "international",
    "global",
    "technologies",
    "systems",
    "solutions",
    "consultancy",
    "consulting",
    "manufacturers",
    "traders",
    "exporters",
    "importers",
    "agency",
    "associates",
    "partners",
    "ventures",
    "pvt",
    "public limited",
    "public ltd",
}

LEGAL_SUFFIX_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in COMPANY_SUFFIXES) + r")\b\.?", re.IGNORECASE
)

INVALID_PATTERNS = [
    r"^undefined$",
    r"^null$",
    r"^none$",
    r"^na$",
    r"^n/a$",
    r"^test",
    r"^demo",
    r"^sample",
    r"^example",
    r"click here",
    r"read more",
    r"learn more",
    r"sign in",
    r"sign up",
    r"log in",
    r"log out",
    r"register",
    r"subscribe",
    r"newsletter",
    r"©?\s*\d{4}",
    r"^\d+$",
    r"^\s*$",
    r"http",
    r"www\.",
    r"\.com",
    r"\.org",
    r"\.net",
    r"home",
    r"about",
    r"contact",
    r"products",
    r"services",
    r"menu",
    r"search",
    r"cart",
    r"checkout",
    r"login",
    r"signup",
    r"register",
    r"forgot",
    r"privacy",
    r"terms",
    r"policy",
    r"^\s*[-–—]\s*$",
    r"^\s*\|\s*$",
]

INVALID_COMBINED = re.compile("|".join(INVALID_PATTERNS), re.IGNORECASE)


def _clean_name(name: str) -> str:
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"^[\s\-–—|.:;]+|[\s\-–—|.:;]+$", "", name)
    name = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", name)
    return name


def _has_invalid_chars(name: str) -> bool:
    if not name:
        return True
    invalid_chars = {"<", ">", "{", "}", "[", "]", "|", "\\", "^", "`", "~"}
    if any(c in invalid_chars for c in name):
        return True
    return False


def _has_sufficient_letters(name: str) -> bool:
    letters = re.sub(r"[^a-zA-Z]", "", name)
    return len(letters) >= 3


def _is_reasonably_formatted(name: str) -> bool:
    if not name:
        return False
    if name[0].isdigit() and len(name) < 10:
        return False
    if name.count("(") != name.count(")"):
        return False
    words = name.split()
    if len(words) > 15:
        return False
    if len(name) > 200:
        return False
    return True


def _score_company_name(name: str, website_domain: Optional[str] = None) -> int:
    score = 0

    if not name:
        return 0

    if _has_invalid_chars(name):
        return 0

    if INVALID_COMBINED.search(name):
        return 0

    if not _has_sufficient_letters(name):
        return 0

    if not _is_reasonably_formatted(name):
        return 0

    score += 1

    clean_name = LEGAL_SUFFIX_PATTERN.sub("", name).strip()
    words = clean_name.split()
    if 2 <= len(words) <= 6:
        score += 2
    elif len(words) == 1 and len(clean_name) >= 4:
        score += 1
    elif len(words) > 6:
        score -= 1

    capitalized_words = [w for w in words if w and w[0].isupper()]
    if len(capitalized_words) / len(words) > 0.7:
        score += 1

    if LEGAL_SUFFIX_PATTERN.search(name):
        score += 1

    if website_domain:
        domain_base = website_domain.lower().replace("www.", "").split(".")[0]
        name_lower = name.lower().replace(" ", "").replace("-", "").replace("_", "")
        if domain_base in name_lower or name_lower in domain_base:
            score += 2

    return max(0, score)


def is_valid_company_name(name: str, website_domain: Optional[str] = None) -> bool:
    if not name:
        return False
    score = _score_company_name(name, website_domain)
    return score >= 3


def extract_best_company_name(
    candidates: List[str], website_domain: Optional[str] = None
) -> str:
    if not candidates:
        return ""

    scored = []
    for name in candidates:
        clean = _clean_name(name)
        if clean:
            score = _score_company_name(clean, website_domain)
            scored.append((score, len(clean), clean))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

    if scored and scored[0][0] >= 3:
        return scored[0][2]

    if scored and scored[0][0] >= 1:
        return scored[0][2]

    return ""


def extract_company_names_from_text(
    text: str, website_domain: Optional[str] = None, max_results: int = 5
) -> List[Tuple[str, int]]:
    if not text:
        return []

    candidates: List[str] = []

    title_match = re.search(r"<title>([^<]+)</title>", text, re.IGNORECASE)
    if title_match:
        candidates.append(title_match.group(1))

    og_title = re.search(r'property="og:title" content="([^"]+)"', text, re.IGNORECASE)
    if og_title:
        candidates.append(og_title.group(1))

    h1_matches = re.findall(r"<h1[^>]*>([^<]+)</h1>", text, re.IGNORECASE)
    candidates.extend(h1_matches)

    lines = text.split("\n")
    for line in lines[:20]:
        line = line.strip()
        if 3 < len(line) < 150:
            if not any(
                x in line.lower()
                for x in ["contact", "email", "phone", "address", "copyright"]
            ):
                if re.match(r"^[A-Z]", line):
                    candidates.append(line)

    seen = set()
    unique = []
    for c in candidates:
        cleaned = _clean_name(c)
        lower = cleaned.lower()
        if lower and lower not in seen:
            seen.add(lower)
            unique.append(cleaned)

    scored = [(name, _score_company_name(name, website_domain)) for name in unique]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [(name, score) for name, score in scored if score >= 3][:max_results]


def clean_company_name(name: str, website_domain: Optional[str] = None) -> str:
    if not name:
        return ""

    cleaned = _clean_name(name)

    if not is_valid_company_name(cleaned, website_domain):
        return ""

    return cleaned
