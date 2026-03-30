"""Natural language query parser.

Converts free-text queries like "toys manufacturer in kolkata, india"
into structured (keyword, location, country) tuples for the scraper engine.
"""

from __future__ import annotations

import re
from typing import Tuple

INDIAN_CITIES = [
    "kolkata", "calcutta", "mumbai", "bombay", "delhi", "new delhi",
    "bangalore", "bengaluru", "hyderabad", "chennai", "madras", "pune",
    "ahmedabad", "surat", "jaipur", "lucknow", "kanpur", "nagpur",
    "jamshedpur", "durgapur", "howrah", "siliguri", "asansol",
    "bardhaman", "bhubaneswar", "kochi", "cochin", "coimbatore",
    "indore", "patna", "vadodara", "baroda", "ghaziabad", "ludhiana",
    "agra", "nashik", "faridabad", "meerut", "rajkot", "varanasi",
    "aurangabad", "amritsar", "jabalpur", "vijayawada", "guwahati",
    "chandigarh", "hubli", "mysore", "jodhpur", "ranchi", "raipur",
    "thiruvananthapuram", "trivandrum", "vizag", "visakhapatnam",
    "mangalore", "mangaluru", "tiruchirappalli", "trichy", "salem",
    "tiruppur", "tirupur", "dehradun", "allahabad", "prayagraj",
    "noida", "gurugram", "gurgaon", "thane", "navi mumbai", "vapi",
    "haldia", "kharagpur", "dankuni", "uluberia", "serampore",
]

COUNTRY_NAMES = [
    "india", "usa", "us", "uk", "united kingdom", "united states",
    "canada", "australia", "germany", "france", "singapore", "uae",
    "dubai", "china", "japan", "south korea",
]

LOCATION_PREPOSITIONS = re.compile(
    r"\b(?:in|at|from|near|based in|located in|situated in)\s+",
    re.IGNORECASE,
)


def parse_nl_query(query: str) -> Tuple[str, str, str]:
    """Parse a natural language query into (keyword, location, country).

    Examples::

        parse_nl_query("toys manufacturer in kolkata, india")
        # → ("toys manufacturer", "kolkata", "india")

        parse_nl_query("software companies bangalore")
        # → ("software companies", "bangalore", "")

        parse_nl_query("steel manufacturers")
        # → ("steel manufacturers", "", "")
    """
    query = query.strip()

    # Pattern: "<keyword> in <city>, <country>" or "<keyword> in <city>"
    loc_match = re.search(
        r"\b(?:in|at|from|near|based\s+in|located\s+in|situated\s+in)\s+"
        r"([a-zA-Z][a-zA-Z\s]{1,30}?)(?:\s*,\s*([a-zA-Z][a-zA-Z\s]{1,20}?))?$",
        query,
        re.IGNORECASE,
    )

    if loc_match:
        raw_loc = loc_match.group(1).strip().rstrip(",").strip()
        raw_country = (loc_match.group(2) or "").strip()
        keyword = query[: loc_match.start()].strip()

        # Validate that the extracted location is a known city or country
        loc_lower = raw_loc.lower()
        country_lower = raw_country.lower()
        is_known_loc = (
            any(city in loc_lower for city in INDIAN_CITIES)
            or any(c in loc_lower for c in COUNTRY_NAMES)
        )
        if is_known_loc:
            # If the "city" part is actually a country, swap
            if any(c == loc_lower for c in COUNTRY_NAMES) and not raw_country:
                return keyword, "", raw_loc
            country = raw_country if raw_country else (
                "india" if any(city in loc_lower for city in INDIAN_CITIES) else ""
            )
            return keyword, raw_loc, country

    # Fallback: check if the query ends with a known city name
    query_lower = query.lower()
    for city in sorted(INDIAN_CITIES, key=len, reverse=True):
        if query_lower.endswith(f" {city}"):
            keyword = query[: -(len(city) + 1)].strip()
            return keyword, city, "india"

    # No location found — return the full query as keyword
    return query, "", ""


def enrich_query_input(keyword: str, location: str, industry: str) -> Tuple[str, str, str]:
    """If keyword looks like a natural language query (contains a city/country),
    parse it and merge with any explicitly provided location/industry.

    Returns (keyword, location, industry).
    """
    parsed_kw, parsed_loc, _parsed_country = parse_nl_query(keyword)

    # Only apply NL parsing if something was extracted
    if parsed_loc and not location:
        return parsed_kw, parsed_loc, industry
    return keyword, location, industry
