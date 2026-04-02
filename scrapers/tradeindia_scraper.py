from __future__ import annotations

import urllib.parse
from typing import Dict, List

from bs4 import BeautifulSoup
from loguru import logger

from extractors.email_extractor import extract_emails
from extractors.phone_extractor import extract_phones
from scrapers.base_scraper import BaseScraper

DDG_POST_URL = "https://html.duckduckgo.com/html/"


def _ddg_captcha(html: str) -> bool:
    return "bots use DuckDuckGo" in html or "Select all squares" in html


def _decode_ddg_href(href: str) -> str:
    if "duckduckgo.com/l/?" in href or href.startswith("//duckduckgo.com/l/?"):
        if href.startswith("//"):
            href = "https:" + href
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        if "uddg" in parsed:
            return urllib.parse.unquote(parsed["uddg"][0])
    return href


class TradeIndiaScraper(BaseScraper):
    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:
        # Search for TradeIndia company pages via DuckDuckGo site: filter
        site_query = f"{query} site:tradeindia.com"
        logger.info(f"TradeIndia DDG search: '{site_query}'")

        try:
            html = await self.request_manager.post_form(
                DDG_POST_URL,
                data={"q": site_query, "b": "", "kl": "in-en"},
            )
        except Exception as exc:
            logger.warning(f"TradeIndia DDG search failed for '{query}': {exc}")
            return []

        if _ddg_captcha(html):
            logger.warning(f"DDG CAPTCHA triggered for TradeIndia search '{query}' — skipping")
            return []

        soup = BeautifulSoup(html, "lxml")
        result_items = (
            soup.select("div.result__body")
            or soup.select("div.results_links_deep")
            or soup.select("div.result")
        )

        records: List[Dict[str, str]] = []
        for div in result_items[:12]:
            title_el = (
                div.select_one("a.result__a")
                or div.select_one("h2.result__title a")
                or div.select_one("h2 a")
            )
            if not title_el:
                continue

            raw_href = title_el.get("href") or ""
            href = _decode_ddg_href(raw_href)

            if not href.startswith("http"):
                continue
            if "tradeindia.com" not in href:
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

            # Try to fetch the TradeIndia company page for more details
            address = ""
            industry_type = ""
            try:
                page_html = await self.request_manager.fetch(href)
                p_soup = BeautifulSoup(page_html, "lxml")
                page_text = p_soup.get_text(" ", strip=True)

                if not phones:
                    phones = extract_phones(page_text)
                if not emails:
                    emails = extract_emails(page_text)

                # TradeIndia profile table rows
                for row in p_soup.select("tr, li.detail-item, div.company-details div"):
                    row_text = row.get_text(" ", strip=True).lower()
                    tds = row.select("td, span, div")
                    if "nature of business" in row_text or "company type" in row_text:
                        if len(tds) > 1:
                            industry_type = tds[-1].get_text(strip=True)
                    if "address" in row_text and not address:
                        if len(tds) > 1:
                            address = tds[-1].get_text(strip=True)

                # Fallback: look for address in meta/structured data
                if not address:
                    addr_el = p_soup.select_one(
                        ".company-address, .address, [itemprop='address'], .seller-address"
                    )
                    if addr_el:
                        address = addr_el.get_text(" ", strip=True)

                # Better name from page title
                page_title = p_soup.find("title")
                if page_title:
                    t = page_title.get_text(strip=True).split("-")[0].strip()
                    if t and len(t) > 3:
                        name = t
            except Exception:
                pass

            record = self.build_record(
                company_name=name,
                website=href,
                description=description[:400],
                email=emails[0] if emails else "",
                phone=phones[0] if phones else "",
                address=address,
                industry=industry_type,
                industry_type=industry_type,
                source="tradeindia",
                additional_info=f"TradeIndia via DDG for: {query}",
            )
            records.append(record)

        logger.info(f"TradeIndia returned {len(records)} records for '{query}'")
        return records
