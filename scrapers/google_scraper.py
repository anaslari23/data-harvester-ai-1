from __future__ import annotations

import os
import urllib.parse
from typing import Dict, List

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from extractors.email_extractor import extract_emails
from extractors.phone_extractor import extract_phones
from scrapers.base_scraper import BaseScraper

# Google Custom Search API
_CSE_URL = "https://www.googleapis.com/customsearch/v1"

# DuckDuckGo HTML fallback
_DDG_POST_URL = "https://html.duckduckgo.com/html/"


def _decode_ddg_href(href: str) -> str:
    """Decode DuckDuckGo redirect wrapper URLs."""
    if "duckduckgo.com/l/?" in href or href.startswith("//duckduckgo.com/l/?"):
        if href.startswith("//"):
            href = "https:" + href
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        if "uddg" in parsed:
            return urllib.parse.unquote(parsed["uddg"][0])
    return href


def _ddg_captcha(html: str) -> bool:
    """Return True if DDG is serving a CAPTCHA / bot-challenge page."""
    return "bots use DuckDuckGo" in html or "Select all squares" in html


class GoogleScraper(BaseScraper):

    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:
        # ── Primary: Google Custom Search Engine API ──────────────────────
        api_key = os.getenv("GOOGLE_SEARCH_API_KEY", "").strip()
        cx = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "").strip()

        if api_key and cx:
            records = await self._cse_search(query, api_key, cx)
            if records:
                logger.info(f"Google CSE returned {len(records)} records for '{query}'")
                return records
            logger.warning(f"Google CSE returned 0 for '{query}', falling back to DDG")

        # ── Fallback: DuckDuckGo HTML (POST) ─────────────────────────────
        return await self._ddg_search(query)

    # ── Google CSE ─────────────────────────────────────────────────────────

    async def _cse_search(self, query: str, api_key: str, cx: str) -> List[Dict[str, str]]:
        params = {
            "q": query,
            "key": api_key,
            "cx": cx,
            "num": "10",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(_CSE_URL, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.warning(f"Google CSE HTTP {resp.status} for '{query}': {body[:200]}")
                        return []
                    data = await resp.json()
        except Exception as exc:
            logger.warning(f"Google CSE request failed for '{query}': {exc}")
            return []

        items = data.get("items", [])
        records: List[Dict[str, str]] = []

        for item in items:
            href = item.get("link", "")
            if not href.startswith("http"):
                continue

            name = item.get("title", "")
            description = item.get("snippet", "")
            emails = extract_emails(description)
            phones = extract_phones(description)

            # Enrich from the actual page
            profile_data: Dict[str, str] = {}
            try:
                profile_data = await self.enrich_from_profile(href, "Search")
            except Exception:
                pass

            record = self.build_record(
                company_name=name,
                website=href,
                description=description,
                email=emails[0] if emails else "",
                phone=phones[0] if phones else "",
                source="google",
                additional_info=f"Google CSE result for: {query}",
            )
            records.append(self.merge_records(record, profile_data))

        return records

    # ── DuckDuckGo fallback ────────────────────────────────────────────────

    async def _ddg_search(self, query: str) -> List[Dict[str, str]]:
        try:
            html = await self.request_manager.post_form(
                _DDG_POST_URL,
                data={"q": query, "b": "", "kl": "in-en"},
            )
        except Exception as exc:
            logger.warning(f"DDG search failed for '{query}': {exc}")
            return []

        if _ddg_captcha(html):
            logger.warning(f"DDG CAPTCHA triggered for '{query}' — skipping")
            return []

        soup = BeautifulSoup(html, "lxml")
        result_items = (
            soup.select("div.result__body")
            or soup.select("div.results_links_deep")
            or soup.select("div.result")
        )

        records: List[Dict[str, str]] = []
        for div in result_items[:10]:
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
            description = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            emails = extract_emails(description)
            phones = extract_phones(description)

            profile_data: Dict[str, str] = {}
            try:
                profile_data = await self.enrich_from_profile(href, "Search")
            except Exception:
                pass

            record = self.build_record(
                company_name=name,
                website=href,
                description=description,
                email=emails[0] if emails else "",
                phone=phones[0] if phones else "",
                source="google",
                additional_info=f"DDG search result for: {query}",
            )
            records.append(self.merge_records(record, profile_data))

        logger.info(f"DDG returned {len(records)} records for '{query}'")
        return records
