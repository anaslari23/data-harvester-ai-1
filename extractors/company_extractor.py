import re

EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
PHONE_REGEX = r"\+?\d[\d\s\-]{7,}\d"

def parse_company_page(text, website):

    emails = list(set(re.findall(EMAIL_REGEX, text)))
    phones = list(set(re.findall(PHONE_REGEX, text)))

    return {
        "Company Name": website,
        "Website": website,
        "Phone Number": ", ".join(phones[:3]),
        "EMail Address": ", ".join(emails[:3])
    }
