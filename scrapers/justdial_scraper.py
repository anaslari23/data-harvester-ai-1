from __future__ import annotations

import re
import urllib.parse
from typing import Dict, List

from bs4 import BeautifulSoup
from loguru import logger

from extractors.email_extractor import extract_emails
from extractors.phone_extractor import extract_phones
from scrapers.base_scraper import BaseScraper

DDG_POST_URL = "https://html.duckduckgo.com/html/"

# JustDial listing URL patterns to accept
_JD_LISTING_RE = re.compile(
    r"justdial\.com/[^/]+/[^/]+-(?:in|near|at|around)-[^/]+",
    re.IGNORECASE,
)
_JD_CATEGORY_RE = re.compile(
    r"justdial\.com/[A-Za-z]+/[A-Za-z][^?#]{5,}/nct-",
    re.IGNORECASE,
)


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


def _is_jd_listing(url: str) -> bool:
    return bool(_JD_LISTING_RE.search(url) or _JD_CATEGORY_RE.search(url))


class JustDialScraper(BaseScraper):
    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:
        # Search for JustDial listing pages via DuckDuckGo site: filter
        site_query = f"{query} site:justdial.com"
        logger.info(f"JustDial DDG search: '{site_query}'")

        try:
            html = await self.request_manager.post_form(
                DDG_POST_URL,
                data={"q": site_query, "b": "", "kl": "in-en"},
            )
        except Exception as exc:
            logger.warning(f"JustDial DDG search failed for '{query}': {exc}")
            return []

        if _ddg_captcha(html):
            logger.warning(f"DDG CAPTCHA triggered for JustDial search '{query}' — skipping")
            return []

        soup = BeautifulSoup(html, "lxml")
        result_items = (
            soup.select("div.result__body")
            or soup.select("div.results_links_deep")
            or soup.select("div.result")
        )

        records: List[Dict[str, str]] = []
        seen_urls: set = set()

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
            if "justdial.com" not in href:
                continue
            if "duckduckgo.com" in href:
                continue
            if href in seen_urls:
                continue
            seen_urls.add(href)

            name = title_el.get_text(" ", strip=True)
            snippet_el = (
                div.select_one("a.result__snippet")
                or div.select_one(".result__snippet")
                or div.select_one("p")
            )
            description = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            emails = extract_emails(description)
            phones = extract_phones(description)

            # For listing pages (multiple companies), try to parse individual entries
            if _is_jd_listing(href):
                listing_records = await self._parse_jd_listing_page(href, query)
                if listing_records:
                    records.extend(listing_records)
                    continue

            # Single company page
            address = ""
            category = ""
            try:
                page_html = await self.request_manager.fetch(href)
                p_soup = BeautifulSoup(page_html, "lxml")
                page_text = p_soup.get_text(" ", strip=True)

                if not phones:
                    phones = extract_phones(page_text)
                if not emails:
                    emails = extract_emails(page_text)

                addr_el = p_soup.select_one(
                    ".address, [itemprop='address'], .cont_fl_addr, .jdl_addr"
                )
                if addr_el:
                    address = addr_el.get_text(" ", strip=True)

                cat_el = p_soup.select_one(".cat_name, .cate, [itemprop='description']")
                if cat_el:
                    category = cat_el.get_text(" ", strip=True)

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
                industry=category,
                industry_type=category,
                source="justdial",
                additional_info=f"JustDial via DDG for: {query}",
            )
            records.append(record)

        logger.info(f"JustDial returned {len(records)} records for '{query}'")
        return records

    async def _parse_jd_listing_page(self, url: str, query: str) -> List[Dict[str, str]]:
        """Attempt to extract individual company entries from a JustDial listing page."""
        records: List[Dict[str, str]] = []
        try:
            html = await self.request_manager.fetch(url)
            soup = BeautifulSoup(html, "lxml")

            # JustDial uses various card selectors across versions
            cards = (
                soup.select("li.cntanr")
                or soup.select(".jdCard")
                or soup.select(".resultbox_info")
                or soup.select("[class*='store-details']")
                or soup.select("div.jresult")
            )

            for card in cards[:15]:
                name_el = card.select_one(
                    "span.jcn a, .resultbox_title_anchor, .jdTitle a, "
                    ".title a, h2.title, .fn.org, .store-name"
                )
                if not name_el:
                    continue
                name = name_el.get_text(" ", strip=True)
                if not name or len(name) < 3:
                    continue

                card_text = card.get_text(" ", strip=True)
                phones = extract_phones(card_text)
                emails = extract_emails(card_text)

                addr_el = card.select_one(
                    "span.cont_fl_addr, .resultbox_address, .address, .adr"
                )
                address = addr_el.get_text(" ", strip=True) if addr_el else ""

                cat_el = card.select_one("span.cate, .resultbox_category, .cat_name")
                category = cat_el.get_text(" ", strip=True) if cat_el else ""

                # Try to get company's own website from card links
                company_website = ""
                for a in card.select("a[href]"):
                    href = a.get("href", "")
                    if href.startswith("http") and "justdial.com" not in href:
                        company_website = href
                        break

                record = self.build_record(
                    company_name=name,
                    website=company_website or url,
                    phone=phones[0] if phones else "",
                    email=emails[0] if emails else "",
                    address=address,
                    industry=category,
                    industry_type=category,
                    source="justdial",
                    additional_info=f"JustDial listing: {url} | query: {query}",
                )
                records.append(record)
        except Exception as exc:
            logger.debug(f"JD listing parse failed for {url}: {exc}")
        return records
