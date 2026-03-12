from bs4 import BeautifulSoup
import re


EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
PHONE_REGEX = r"\+?\d[\d\s\-]{8,}\d"


def normalize_text(text: str) -> str:
    """Clean excessive whitespace and formatting."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def extract_emails(text: str):
    """Extract unique email addresses."""
    matches = re.findall(EMAIL_REGEX, text or "")
    cleaned = {m.strip().lower() for m in matches if len(m) < 100}
    return sorted(cleaned)


def extract_phones(text: str):
    """Extract and clean phone numbers."""
    raw_matches = re.findall(PHONE_REGEX, text or "")

    cleaned_numbers = set()

    for number in raw_matches:

        # Remove non-digit characters except +
        normalized = re.sub(r"[^\d+]", "", number)

        digits = re.sub(r"\D", "", normalized)

        # Filter unrealistic numbers
        if 9 <= len(digits) <= 15:
            cleaned_numbers.add(normalized)

    return sorted(cleaned_numbers)


def parse_html(html: str):
    """Parse HTML and extract structured contact info."""

    if not html:
        return {
            "title": "",
            "emails": [],
            "phones": [],
            "text": ""
        }

    soup = BeautifulSoup(html, "lxml")

    title = ""
    if soup.title and soup.title.string:
        title = normalize_text(soup.title.string)

    text = normalize_text(soup.get_text(" ", strip=True))

    emails = extract_emails(text)
    phones = extract_phones(text)

    return {
        "title": title,
        "emails": emails,
        "phones": phones,
        "text": text[:1000]  # limit for downstream processing
    }