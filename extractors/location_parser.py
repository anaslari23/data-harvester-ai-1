from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


INDIAN_STATES = {
    "andhra pradesh",
    "arunachal pradesh",
    "assam",
    "bihar",
    "chhattisgarh",
    "goa",
    "gujarat",
    "haryana",
    "himachal pradesh",
    "jharkhand",
    "karnataka",
    "kerala",
    "madhya pradesh",
    "maharashtra",
    "manipur",
    "meghalaya",
    "mizoram",
    "nagaland",
    "odisha",
    "punjab",
    "rajasthan",
    "sikkim",
    "tamil nadu",
    "telangana",
    "tripura",
    "uttar pradesh",
    "uttarakhand",
    "west bengal",
    "delhi",
    "jammu and kashmir",
    "ladakh",
    "andaman and nicobar islands",
    "chandigarh",
    "dadra and nagar haveli",
    "daman and diu",
    "lakshadweep",
    "puducherry",
}

STATE_ABBREVIATIONS: Dict[str, str] = {
    "ap": "Andhra Pradesh",
    "ar": "Arunachal Pradesh",
    "as": "Assam",
    "br": "Bihar",
    "cg": "Chhattisgarh",
    "dl": "Delhi",
    "ga": "Goa",
    "gj": "Gujarat",
    "hp": "Himachal Pradesh",
    "hr": "Haryana",
    "jh": "Jharkhand",
    "jk": "Jammu and Kashmir",
    "ka": "Karnataka",
    "kl": "Kerala",
    "ld": "Ladakh",
    "mh": "Maharashtra",
    "ml": "Meghalaya",
    "mn": "Manipur",
    "mp": "Madhya Pradesh",
    "mz": "Mizoram",
    "nl": "Nagaland",
    "od": "Odisha",
    "or": "Odisha",
    "pb": "Punjab",
    "py": "Puducherry",
    "rj": "Rajasthan",
    "sk": "Sikkim",
    "tn": "Tamil Nadu",
    "ts": "Telangana",
    "tr": "Tripura",
    "up": "Uttar Pradesh",
    "uk": "Uttarakhand",
    "wb": "West Bengal",
}

COMMON_COUNTRIES: Dict[str, str] = {
    "india": "India",
    "usa": "United States",
    "us": "United States",
    "uk": "United Kingdom",
    "gb": "United Kingdom",
    "uae": "United Arab Emirates",
    "germany": "Germany",
    "france": "France",
    "canada": "Canada",
    "ca": "Canada",
    "australia": "Australia",
    "au": "Australia",
    "singapore": "Singapore",
    "sg": "Singapore",
    "japan": "Japan",
    "china": "China",
    "br": "Brazil",
    "mx": "Mexico",
    "nl": "Netherlands",
    "es": "Spain",
    "it": "Italy",
    "de": "Germany",
    "ru": "Russia",
    "kr": "South Korea",
    "za": "South Africa",
    "ae": "United Arab Emirates",
    "ph": "Philippines",
    "my": "Malaysia",
    "th": "Thailand",
    "vn": "Vietnam",
    "id": "Indonesia",
    "eg": "Egypt",
    "pk": "Pakistan",
    "bd": "Bangladesh",
    "lk": "Sri Lanka",
}

US_STATES: Dict[str, str] = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
    "dc": "DC",
}

UK_COUNTIES = {
    "bedfordshire",
    "berkshire",
    "bristol",
    "buckinghamshire",
    "cambridgeshire",
    "cheshire",
    "cornwall",
    "cumbria",
    "derbyshire",
    "devon",
    "dorset",
    "durham",
    "east yorkshire",
    "east sussex",
    "essex",
    "gloucestershire",
    "greater london",
    "greater manchester",
    "hampshire",
    "herefordshire",
    "hertfordshire",
    "isle of wight",
    "kent",
    "lancashire",
    "leicestershire",
    "lincolnshire",
    "london",
    "norfolk",
    "north yorkshire",
    "northamptonshire",
    "northumberland",
    "nottinghamshire",
    "oxfordshire",
    "rutland",
    "shropshire",
    "somerset",
    "south yorkshire",
    "staffordshire",
    "suffolk",
    "surrey",
    "tyne and wear",
    "warwickshire",
    "west midlands",
    "west sussex",
    "west yorkshire",
    "wiltshire",
    "worcestershire",
}

CANADIAN_PROVINCES = {
    "alberta": "AB",
    "british columbia": "BC",
    "manitoba": "MB",
    "new brunswick": "NB",
    "newfoundland and labrador": "NL",
    "nova scotia": "NS",
    "ontario": "ON",
    "prince edward island": "PE",
    "quebec": "QC",
    "saskatchewan": "SK",
    "northwest territories": "NT",
    "nunavut": "NU",
    "yukon": "YT",
}

PINCODE_PATTERN = re.compile(r"\b\d{6}\b")
US_ZIP_PATTERN = re.compile(r"\b\d{5}(?:-\d{4})?\b")
UK_POSTCODE_PATTERN = re.compile(
    r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", re.IGNORECASE
)

STATE_PATTERN = re.compile(r"\b(" + "|".join(INDIAN_STATES) + r")\b", re.IGNORECASE)
US_STATE_PATTERN = re.compile(
    r"\b(" + "|".join(US_STATES.keys()) + r")\b", re.IGNORECASE
)
UK_COUNTY_PATTERN = re.compile(r"\b(" + "|".join(UK_COUNTIES) + r")\b", re.IGNORECASE)
CANADA_PROVINCE_PATTERN = re.compile(
    r"\b(" + "|".join(CANADIAN_PROVINCES.keys()) + r")\b", re.IGNORECASE
)

COUNTRY_PATTERN = re.compile(
    r"\b(" + "|".join(COMMON_COUNTRIES.keys()) + r")\b", re.IGNORECASE
)

CITY_ALIASES: Dict[str, str] = {
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "gauhati": "Guwahati",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "poona": "Pune",
    "secunderabad": "Hyderabad",
    "new delhi": "Delhi",
    "delhi ncr": "Delhi",
    "ncr": "Delhi",
}

KNOWN_CITIES: set = {
    "mumbai",
    "delhi",
    "bengaluru",
    "bangalore",
    "chennai",
    "hyderabad",
    "pune",
    "kolkata",
    "ahmedabad",
    "jaipur",
    "lucknow",
    "kanpur",
    "nagpur",
    "indore",
    "bhopal",
    "patna",
    "gurgaon",
    "gauhati",
    "guwahati",
    "surat",
    "vadodara",
    "kochi",
    "ludhiana",
    "agra",
    "meerut",
    "nashik",
    "faridabad",
    "ranchi",
    "raipur",
    "dehradun",
    "haridwar",
    "visakhapatnam",
    "vijayawada",
    "tirupati",
    "nellore",
    "coimbatore",
    "madurai",
    "trichy",
    "salem",
    "tirunelveli",
    "vellore",
    "mangalore",
    "mysore",
    "hubli",
    "belgaum",
    "dhanbad",
    "jamshedpur",
    "asansol",
    "durgapur",
    "howrah",
    "siliguri",
    "bhubaneswar",
    "cuttack",
    "bokaro",
    "varanasi",
    "prayagraj",
    "aligarh",
    "mathura",
    "agartala",
    "imphal",
    "shillong",
    "itanagar",
    "gangtok",
    "thiruvananthapuram",
    "kottayam",
    "thrissur",
    "ernakulam",
    "kollam",
}

US_CITIES: set = {
    "new york",
    "los angeles",
    "chicago",
    "houston",
    "phoenix",
    "philadelphia",
    "san antonio",
    "san diego",
    "dallas",
    "san jose",
    "austin",
    "jacksonville",
    "fort worth",
    "columbus",
    "charlotte",
    "san francisco",
    "indianapolis",
    "seattle",
    "denver",
    "boston",
    "detroit",
    "el paso",
    "memphis",
    "nashville",
    "portland",
    "oklahoma city",
    "las vegas",
    "louisville",
    "baltimore",
    "milwaukee",
    "albuquerque",
    "tucson",
    "fresno",
    "mesa",
    "sacramento",
    "atlanta",
    "kansas city",
    "colorado springs",
    "miami",
    "raleigh",
    "omaha",
    "long beach",
    "virginia beach",
    "oakland",
    "minneapolis",
    "tulsa",
    "arlington",
    "tampa",
    "new orleans",
}

UK_CITIES: set = {
    "london",
    "birmingham",
    "manchester",
    "glasgow",
    "liverpool",
    "leeds",
    "sheffield",
    "edinburgh",
    "bristol",
    "manchester",
    "cardiff",
    "belfast",
    "nottingham",
    "southampton",
    "brighton",
    "leicester",
    "oxford",
    "cambridge",
    "coventry",
    "york",
}

SKIP_WORDS = {
    "street",
    "road",
    "lane",
    "avenue",
    "sector",
    "phase",
    "building",
    "floor",
    "plot",
    "near",
    "opposite",
    "behind",
    "station",
    "area",
    "nagar",
    "colony",
    "village",
    "town",
    "city",
    "district",
    "block",
    "tower",
    "park",
    "estate",
    "premises",
    "chambers",
    "office",
    "division",
    "tech",
    "corporate",
    "head",
    "branch",
    "center",
    "centre",
    "complex",
    "suite",
    "room",
    "market",
    "house",
}


def parse_address_components(address: str) -> Dict[str, str]:
    if not address:
        return {"city": "", "state": "", "country": "India", "pincode": ""}

    address_lower = address.lower()
    components: Dict[str, str] = {
        "city": "",
        "state": "",
        "country": "India",
        "pincode": "",
    }

    us_state_match = US_STATE_PATTERN.search(address_lower)
    if us_state_match:
        components["state"] = US_STATES.get(us_state_match.group(1).lower(), "")
        components["country"] = "United States"

    uk_county_match = UK_COUNTY_PATTERN.search(address_lower)
    if uk_county_match and not components.get("state"):
        components["state"] = uk_county_match.group(1).title()
        components["country"] = "United Kingdom"

    canada_province_match = CANADA_PROVINCE_PATTERN.search(address_lower)
    if canada_province_match:
        components["state"] = CANADIAN_PROVINCES.get(
            canada_province_match.group(1).lower(), ""
        )
        components["country"] = "Canada"

    state_match = STATE_PATTERN.search(address_lower)
    if state_match:
        components["state"] = state_match.group(1).title()
        components["country"] = "India"

    country_match = COUNTRY_PATTERN.search(address_lower)
    if country_match:
        country_key = country_match.group(1).lower()
        components["country"] = COMMON_COUNTRIES.get(country_key, country_key.title())

    uk_postcode_match = UK_POSTCODE_PATTERN.search(address)
    if uk_postcode_match:
        components["pincode"] = uk_postcode_match.group(0).upper()

    us_zip_match = US_ZIP_PATTERN.search(address)
    if us_zip_match:
        components["pincode"] = us_zip_match.group(0)

    pincode_match = PINCODE_PATTERN.search(address)
    if pincode_match:
        components["pincode"] = pincode_match.group(0)

    for known_city in KNOWN_CITIES | US_CITIES | UK_CITIES:
        if known_city in address_lower:
            canonical_city = CITY_ALIASES.get(known_city, known_city.title())
            components["city"] = canonical_city
            break

    if not components["city"]:
        _extract_city_from_parts(address, components)

    return components


def _extract_city_from_parts(address: str, components: Dict[str, str]) -> None:
    parts = re.split(r"[,|\-\n]", address)
    for part in parts:
        part = part.strip()
        part_lower = part.lower()

        if len(part) > 3 and len(part) < 40:
            if not any(skip in part_lower for skip in SKIP_WORDS):
                if not any(state.lower() in part_lower for state in INDIAN_STATES):
                    if not any(
                        country.lower() in part_lower
                        for country in COMMON_COUNTRIES.keys()
                    ):
                        if not any(s.lower() in part_lower for s in US_STATES.keys()):
                            if not any(
                                c.lower() in part_lower
                                for c in CANADIAN_PROVINCES.keys()
                            ):
                                if re.search(r"\d", part) and not re.search(
                                    r"\d{6}", part
                                ):
                                    continue
                                if (
                                    len(part) > 4
                                    and part[0].isupper()
                                    and part[1].islower()
                                ):
                                    if len(part.split()) <= 2:
                                        components["city"] = part.title()
                                        break


def parse_full_address(address: str) -> Tuple[str, str, str, str]:
    if not address:
        return ("", "", "", "")

    components = parse_address_components(address)
    city = components.get("city", "")

    city_lower = city.lower() if city else ""
    invalid_city_indicators = {
        "ppg division",
        "corporate office",
        "head office",
        "branch office",
        "tech village",
        "tech park",
        "building",
        "tower",
        "block",
        "sector",
        "phase",
        "plot",
        "industrial area",
        "estate",
        "premises",
        "chambers",
        "floor",
        "suite",
        "room",
        "near",
        "opposite",
        "behind",
        "station",
        "road",
        "lane",
        "street",
        "market",
        "nagar",
        "colony",
    }

    if city and any(indicator in city_lower for indicator in invalid_city_indicators):
        city = ""

    return (
        city,
        components.get("state", ""),
        components.get("country", ""),
        components.get("pincode", ""),
    )


def extract_location_from_text(text: str) -> Dict[str, str]:
    result = {"city": "", "state": "", "country": "India"}

    if not text:
        return result

    text_lower = text.lower()

    city_patterns = [
        r"\b(mumbai|delhi|bangalore|bengaluru|chennai|hyderabad|pune|kolkata|ahmedabad|jaipur|lucknow|kanpur|nagpur|indore|bhopal|patna|gurgaon|surat|vadodara|kochi|ludhiana|agra|meerut|nashik|faridabad)\b",
        r"\b(new york|los angeles|chicago|houston|phoenix|philadelphia|san antonio|san diego|dallas|san jose|austin|jacksonville)\b",
        r"\b(london|birmingham|manchester|glasgow|liverpool|leeds|sheffield|edinburgh|bristol)\b",
        r"(?:located in|headquartered in|based in|city[:\s]+)([a-zA-Z\s]+?)(?:,|\.|$)",
        r"address[:\s]+([a-zA-Z\s,]+?)(?:,|\.|$)",
    ]

    for pattern in city_patterns:
        match = re.search(pattern, text_lower)
        if match:
            city = match.group(1).strip() if match.lastindex else match.group(0).strip()
            if len(city) > 2 and len(city) < 40:
                result["city"] = city.title()
                break

    state_match = STATE_PATTERN.search(text_lower)
    if state_match:
        result["state"] = state_match.group(1).title()

    us_state_match = US_STATE_PATTERN.search(text_lower)
    if us_state_match:
        result["state"] = US_STATES.get(us_state_match.group(1).lower(), "")
        result["country"] = "United States"

    country_match = COUNTRY_PATTERN.search(text_lower)
    if country_match:
        country_key = country_match.group(1).lower()
        result["country"] = COMMON_COUNTRIES.get(country_key, country_key.title())

    return result


def enrich_record_with_location(record: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(record)

    if not enriched.get("address") and not enriched.get("city"):
        combined = " ".join(
            [
                str(enriched.get("additional_info", "")),
                str(enriched.get("description", "")),
            ]
        )
        location = extract_location_from_text(combined)
        if not enriched.get("city") and location.get("city"):
            enriched["city"] = location["city"]
        if not enriched.get("state") and location.get("state"):
            enriched["state"] = location["state"]
        if not enriched.get("country") and location.get("country"):
            enriched["country"] = location["country"]
    elif enriched.get("address"):
        city, state, country, pincode = parse_full_address(enriched["address"])
        if not enriched.get("city") and city:
            enriched["city"] = city
        if not enriched.get("state") and state:
            enriched["state"] = state
        if not enriched.get("country") and country:
            enriched["country"] = country
        if pincode:
            enriched["pincode"] = pincode

    enriched.setdefault("city", "")
    enriched.setdefault("state", "")
    enriched.setdefault("country", "")

    return enriched
