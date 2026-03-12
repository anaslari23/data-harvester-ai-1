import re
from bs4 import BeautifulSoup


EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
PHONE_REGEX = r"\+?\d[\d\s\-]{8,}\d"

ERP_KEYWORDS = [
    "SAP",
    "Oracle",
    "NetSuite",
    "Odoo",
    "Microsoft Dynamics",
    "Zoho ERP",
    "Tally",
    "Infor",
    "Sage"
]

LEADERSHIP_TITLES = [
    "CEO",
    "Founder",
    "Director",
    "CFO",
    "CTO",
    "VP",
    "Head",
    "Managing Director"
]


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def extract_emails(text):
    return list(set(re.findall(EMAIL_REGEX, text)))


def extract_phones(text):

    raw = re.findall(PHONE_REGEX, text)

    phones = []

    for p in raw:

        digits = re.sub(r"\D", "", p)

        if 9 <= len(digits) <= 15:
            phones.append(p.strip())

    return list(set(phones))


def extract_erp(text):

    found = []

    for erp in ERP_KEYWORDS:

        if erp.lower() in text.lower():
            found.append(erp)

    return list(set(found))


def extract_leadership(text):

    leaders = []

    lines = text.split("\n")

    for line in lines:

        for role in LEADERSHIP_TITLES:

            if role.lower() in line.lower():
                leaders.append(clean_text(line))

    return list(set(leaders))[:5]


def guess_industry(text):

    industry_keywords = {
        "software": "Software / IT",
        "erp": "ERP / Software",
        "manufacturing": "Manufacturing",
        "furniture": "Furniture Manufacturing",
        "logistics": "Logistics",
        "consulting": "Consulting",
        "marketing": "Marketing",
        "education": "Education",
        "health": "Healthcare"
    }

    text = text.lower()

    for k, v in industry_keywords.items():

        if k in text:
            return v

    return ""


def parse_company_page(html, url, sl_no):

    soup = BeautifulSoup(html, "lxml")

    title = soup.title.text if soup.title else ""

    text = soup.get_text("\n")

    text = clean_text(text)

    emails = extract_emails(text)

    phones = extract_phones(text)

    erp = extract_erp(text)

    leaders = extract_leadership(text)

    industry = guess_industry(text)

    data = {

        "SL No.": sl_no,

        "Company Name": clean_text(title),

        "Website": url,

        "Owner/ IT Head/ CEO/Finance Head Name": "; ".join(leaders),

        "Phone Number": "; ".join(phones),

        "EMail Address": "; ".join(emails),

        "Address": "",

        "Industry_Type": industry,

        "Employee _No": "",

        "Branch/ Warehouse _No": "",

        "Annual_Turnover": "",

        "Current_Use_ERP Software_Name": "; ".join(erp),

        "Additional_Information": text[:500]
    }

    return data