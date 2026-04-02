from __future__ import annotations

import urllib.parse
import asyncio
from typing import Dict, List

from bs4 import BeautifulSoup

from extractors.email_extractor import extract_emails
from extractors.phone_extractor import extract_phones
from scrapers.base_scraper import BaseScraper


SEARX_INSTANCES = [
    ("https://searxng.site", "https://searxng.site/search?q={q}&format=html"),
    ("https://search.inetol.net", "https://search.inetol.net/search?q={q}&format=html"),
    ("https://searx.work", "https://searx.work/search?q={q}&format=html"),
    ("https://priv.au", "https://priv.au/search?q={q}&format=html"),
    ("https://etsi.me", "https://etsi.me/search?q={q}&format=html"),
    ("https://searx.tiekoetter.com", "https://searx.tiekoetter.com/search?q={q}&format=html"),
    ("https://opnxng.com", "https://opnxng.com/search?q={q}&format=html"),
    ("https://search.sapti.me", "https://search.sapti.me/search?q={q}&format=html"),
]


class SearxScraper(BaseScraper):
    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        encoded_query = urllib.parse.quote_plus(query)

        for instance_name, url_template in SEARX_INSTANCES:
            try:
                url = url_template.format(q=encoded_query)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                }

                html = await self.request_manager.fetch(url, headers=headers)
                soup = BeautifulSoup(html, "lxml")

                found = False
                for selector in [
                    "article.result",
                    "div.result",
                    ".item",
                    "li.result",
                    "div. Result",
                ]:
                    items = soup.select(selector)
                    if items:
                        for item in items[:15]:
                            title_el = item.select_one(
                                "h3 a, .result_title a, .title a, h2 a, a.result__a"
                            )
                            if not title_el:
                                continue

                            title = title_el.get_text(strip=True)
                            href = title_el.get("href", "")

                            if (
                                not href
                                or href.startswith("#")
                                or "javascript" in href.lower()
                            ):
                                continue

                            content_el = item.select_one(
                                "p, .content, .snippet, .result_content, .result__snippet"
                            )
                            description = (
                                content_el.get_text(strip=True) if content_el else ""
                            )

                            emails = extract_emails(description)
                            phones = extract_phones(description)

                            record = self.build_record(
                                company_name=title,
                                website=href,
                                description=description[:500] if description else "",
                                email=emails[0] if emails else "",
                                phone=phones[0] if phones else "",
                                source="searx",
                                additional_info=f"Found via {instance_name} for: {query}",
                            )
                            results.append(record)
                            found = True

                if found:
                    break

            except Exception:
                continue

        return results
