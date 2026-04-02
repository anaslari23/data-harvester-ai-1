from __future__ import annotations

import re
from typing import Dict, List

from loguru import logger

from core.sources.indiamart_search import IndiaMartSearch
from extractors.email_extractor import extract_emails
from extractors.phone_extractor import extract_phones
from scrapers.base_scraper import BaseScraper


# Common Indian cities — used to split "keyword city" queries
_CITIES = [
    "new delhi", "navi mumbai", "west bengal",
    "kolkata", "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad",
    "chennai", "pune", "ahmedabad", "surat", "jaipur", "lucknow",
    "kanpur", "nagpur", "indore", "thane", "bhopal", "visakhapatnam",
    "patna", "vadodara", "ghaziabad", "ludhiana", "agra", "nashik",
    "ranchi", "faridabad", "meerut", "rajkot", "varanasi", "aurangabad",
    "dhanbad", "amritsar", "howrah", "coimbatore", "jodhpur", "madurai",
    "raipur", "kota", "chandigarh", "guwahati", "solapur", "hubballi",
    "mysuru", "bareilly", "aligarh", "moradabad", "gurgaon", "gurugram",
    "noida", "pimpri", "kalyan", "vasai", "jamshedpur", "durgapur",
    "asansol", "bardhaman", "siliguri", "surat", "coimbatore", "india",
]


def _split_query(query: str):
    """Return (keyword, city) extracted from a plain query string."""
    lower = query.lower()
    for city in sorted(_CITIES, key=len, reverse=True):  # longest match first
        if city in lower:
            keyword = re.sub(re.escape(city), "", lower, flags=re.IGNORECASE).strip(" ,")
            return keyword or query, city
    return query, ""


class IndiaMartScraper(BaseScraper):
    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:
        keyword, city = _split_query(query)
        logger.info(f"IndiaMart search: keyword='{keyword}' city='{city}'")

        im_search = IndiaMartSearch()
        try:
            seeds = await im_search.get_company_urls(keyword, city, max_pages=2)
        except Exception as exc:
            logger.warning(f"IndiaMartSearch failed for '{query}': {exc}")
            return []

        records: List[Dict[str, str]] = []
        for seed in seeds[:20]:
            phone = seed.inline_phone or ""
            email = seed.inline_email or ""
            address = seed.inline_address or ""

            # Derive a display name from the URL path slug (strip query string first)
            from urllib.parse import urlparse as _urlparse
            path = _urlparse(seed.url).path.strip("/")
            slug = path.split("/")[0] if path else ""
            name_guess = slug.replace("-", " ").replace("_", " ").title() if slug else ""

            record = self.build_record(
                company_name=name_guess,
                website=seed.url,
                phone=phone,
                email=email,
                address=address,
                source="indiamart",
                additional_info=f"IndiaMART | {query} | confidence={seed.confidence:.2f}",
            )
            records.append(record)

        logger.info(f"IndiaMart returned {len(records)} records for '{query}'")
        return records
