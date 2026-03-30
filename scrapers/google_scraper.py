from __future__ import annotations

import urllib.parse
from typing import Dict, List

from bs4 import BeautifulSoup

from extractors.email_extractor import extract_emails
from extractors.phone_extractor import extract_phones
from scrapers.base_scraper import BaseScraper

# Using DuckDuckGo HTML — zero bot protection, no JS required
DDG_SEARCH_URL = "https://html.duckduckgo.com/html/?q={query}"

DDG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
    "Referer": "https://duckduckgo.com/",
}

# Maximum search result pages to fetch per query variant
_MAX_RESULTS = 15


def _decode_ddg_href(href: str) -> str:
    """Decode DuckDuckGo redirect URLs to the real destination URL."""
    if href.startswith("//duckduckgo.com/l/?"):
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        if "uddg" in parsed:
            return parsed["uddg"][0]
    return href


def _build_query_variants(query: str) -> List[str]:
    """Return a ranked list of query strings to try, from most to least specific.

    For Indian SME queries we inject contact-oriented terms and directory site:
    dorks so the top results surface company profile pages with phone / email.
    """
    q = query.strip()
    variants = [q]

    q_lower = q.lower()

    # Add contact-enriched variant
    if "contact" not in q_lower and "email" not in q_lower:
        variants.append(f'{q} "contact" OR "email" OR "phone"')

    # Site-specific dorks for high-quality Indian B2B directories
    indian_signals = [
        "india", "kolkata", "mumbai", "delhi", "bangalore", "bengaluru",
        "hyderabad", "chennai", "pune", "ahmedabad", "manufacturer",
        "supplier", "exporter", "wholesaler",
    ]
    if any(sig in q_lower for sig in indian_signals):
        variants.append(f"site:indiamart.com {q}")
        variants.append(f"site:tradeindia.com {q}")
        variants.append(f"site:justdial.com {q}")
        variants.append(f"site:exportersindia.com {q}")

    # Generic directory dorks useful for any geography
    variants.append(f'"{q}" director OR owner OR CEO OR founder')

    return variants


class GoogleScraper(BaseScraper):
    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:
        seen_urls: set[str] = set()
        results: List[Dict[str, str]] = []

        for variant in _build_query_variants(query):
            url = DDG_SEARCH_URL.format(query=urllib.parse.quote_plus(variant))
            html = await self.request_manager.fetch(url, headers=DDG_HEADERS)
            soup = BeautifulSoup(html, "lxml")

            # DDG HTML result containers — try multiple selectors for robustness
            result_items = (
                soup.select("div.result__body")
                or soup.select("div.results_links_deep")
                or soup.select("div.web-result")
            )

            for div in result_items[:_MAX_RESULTS]:
                # Title/link — try multiple known DDG selectors
                title_el = (
                    div.select_one("h2.result__title a.result__a")
                    or div.select_one("a.result__a")
                    or div.select_one("h2 a")
                )
                if not title_el:
                    continue

                raw_href = title_el.get("href") or ""
                href = _decode_ddg_href(raw_href)

                # Skip non-HTTP urls (DDG internal pages, etc.) and duplicates
                if not href.startswith("http"):
                    continue
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                company_name = title_el.get_text(" ", strip=True)

                # Description / snippet
                snippet_el = (
                    div.select_one("a.result__snippet")
                    or div.select_one(".result__snippet")
                    or div.select_one("p")
                )
                description = snippet_el.get_text(" ", strip=True) if snippet_el else ""

                # Quick extraction from snippet text
                emails = extract_emails(description)
                phones = extract_phones(description)

                # Deep enrichment: fetch the actual page
                profile_data: Dict[str, str] = {}
                try:
                    profile_data = await self.enrich_from_profile(href, "Search")
                except Exception:
                    pass

                record = self.build_record(
                    company_name=company_name,
                    website=href,
                    description=description,
                    email=emails[0] if emails else "",
                    phone=phones[0] if phones else "",
                    source="google",
                    additional_info=f"Search result for query: {query}",
                )
                results.append(self.merge_records(record, profile_data))

            # Stop iterating variants once we have enough results
            if len(results) >= _MAX_RESULTS:
                break

        return results
