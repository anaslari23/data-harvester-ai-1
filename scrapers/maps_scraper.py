from __future__ import annotations

import urllib.parse
from typing import Dict, List

from bs4 import BeautifulSoup
from loguru import logger

from extractors.address_extractor import extract_addresses
from extractors.phone_extractor import extract_phones
from scrapers.base_scraper import BaseScraper

# DuckDuckGo HTML endpoint — POST required
_DDG_POST_URL = "https://html.duckduckgo.com/html/"


def _decode_ddg_href(href: str) -> str:
    if "duckduckgo.com/l/?" in href or href.startswith("//duckduckgo.com/l/?"):
        if href.startswith("//"):
            href = "https:" + href
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        if "uddg" in parsed:
            return urllib.parse.unquote(parsed["uddg"][0])
    return href


def _ddg_captcha(html: str) -> bool:
    return "bots use DuckDuckGo" in html or "Select all squares" in html


class MapsScraper(BaseScraper):
    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:
        # Append "address contact location" to bias results toward business listings
        maps_query = f"{query} address contact location"

        try:
            html = await self.request_manager.post_form(
                _DDG_POST_URL,
                data={"q": maps_query, "b": "", "kl": "in-en"},
            )
        except Exception as exc:
            logger.warning(f"Maps DDG search failed for '{query}': {exc}")
            return []

        if _ddg_captcha(html):
            logger.warning(f"DDG CAPTCHA triggered for Maps search '{query}' — skipping")
            return []

        soup = BeautifulSoup(html, "lxml")
        result_items = (
            soup.select("div.result__body")
            or soup.select("div.results_links_deep")
            or soup.select("div.result")
        )

        results: List[Dict[str, str]] = []
        for div in result_items[:8]:
            title_el = (
                div.select_one("h2.result__title a.result__a")
                or div.select_one("a.result__a")
                or div.select_one("h2 a")
            )
            if not title_el:
                continue

            raw_href = title_el.get("href") or ""
            href = _decode_ddg_href(raw_href)

            if not href.startswith("http"):
                continue
            if "duckduckgo.com" in href:
                continue

            name = title_el.get_text(" ", strip=True)
            snippet_el = (
                div.select_one("a.result__snippet")
                or div.select_one(".result__snippet")
                or div.select_one("p")
            )
            snippet_text = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            phones = extract_phones(snippet_text)

            address = ""
            profile_data: Dict[str, str] = {}
            try:
                profile_data = await self.enrich_from_profile(href, "Maps")
                address = profile_data.get("address", "")
                if not address:
                    addresses_from_snippet = extract_addresses(snippet_text)
                    address = addresses_from_snippet[0] if addresses_from_snippet else ""
            except Exception:
                pass

            record = self.build_record(
                company_name=name,
                source="maps",
                website=href,
                phone=phones[0] if phones else profile_data.get("phone", ""),
                email=profile_data.get("email", ""),
                address=address,
                description=snippet_text,
                additional_info=f"Maps result for: {query}",
            )
            results.append(record)

        logger.info(f"Maps returned {len(results)} records for '{query}'")
        return results
