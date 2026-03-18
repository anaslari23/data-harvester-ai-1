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
    "uk": "United Kingdom",
    "uae": "United Arab Emirates",
    "germany": "Germany",
    "france": "France",
    "canada": "Canada",
    "australia": "Australia",
    "singapore": "Singapore",
    "japan": "Japan",
    "china": "China",
    "brazil": "Brazil",
}

PINCODE_PATTERN = re.compile(r"\b\d{6}\b")
STATE_PATTERN = re.compile(r"\b(" + "|".join(INDIAN_STATES) + r")\b", re.IGNORECASE)
COUNTRY_PATTERN = re.compile(
    r"\b(" + "|".join(COMMON_COUNTRIES.keys()) + r")\b", re.IGNORECASE
)
CITY_INDICATORS = re.compile(
    r"\b(city|town|village|district|nagar|mumbai|delhi|bangalore|bengaluru|chennai|hyderabad|pune|kolkata|ahmedabad|jaipur|lucknow|kanpur|nagpur|indore|bhopal|patna|gurgaon|gauhati)\b",
    re.IGNORECASE,
)

CITY_ALIASES = {
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

KNOWN_CITIES = {
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
    "jamshedpur",
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


def parse_address_components(address: str) -> Dict[str, str]:
    if not address:
        return {"city": "", "state": "", "country": ""}

    address_lower = address.lower()
    components: Dict[str, str] = {"city": "", "state": "", "country": ""}

    state_match = STATE_PATTERN.search(address_lower)
    if state_match:
        components["state"] = state_match.group(1).title()

    country_match = COUNTRY_PATTERN.search(address_lower)
    if country_match:
        country_key = country_match.group(1).lower()
        components["country"] = COMMON_COUNTRIES.get(country_key, country_key.title())
    else:
        components["country"] = "India"

    pincode_match = PINCODE_PATTERN.search(address)
    if pincode_match:
        pincode = pincode_match.group(0)
        components["pincode"] = pincode

    for known_city in KNOWN_CITIES:
        if known_city in address_lower:
            canonical_city = CITY_ALIASES.get(known_city, known_city.title())
            components["city"] = canonical_city
            break

    if not components["city"]:
        parts = re.split(r"[,|\-\n]", address)
        for part in parts:
            part = part.strip()
            part_lower = part.lower()

            skip_words = [
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
            ]

            if len(part) > 3 and len(part) < 40:
                if not any(skip in part_lower for skip in skip_words):
                    if not any(state.lower() in part_lower for state in INDIAN_STATES):
                        if not any(
                            country.lower() in part_lower
                            for country in COMMON_COUNTRIES.keys()
                        ):
                            if re.search(r"\d", part) and not re.search(r"\d{6}", part):
                                continue
                            if (
                                len(part) > 4
                                and part[0].isupper()
                                and part[1].islower()
                            ):
                                if len(part.split()) <= 2:
                                    components["city"] = part.title()
                                    break

    return components


def parse_full_address(address: str) -> Tuple[str, str, str, str]:
    if not address:
        return ("", "", "", "")

    components = parse_address_components(address)
    city = components.get("city", "")

    city_lower = city.lower()
    invalid_city_indicators = [
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
    ]

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
        r"\b(mumbai|delhi|bangalore|bengaluru|chennai|hyderabad|pune|kolkata|ahmedabad|jaipur|lucknow|kanpur|nagpur|indore|bhopal|patna|gurgaon|gauhati|surat|vadodara|kochi|ludhiana|agra|meerut|nashik|faridabad|meerut)\b",
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
