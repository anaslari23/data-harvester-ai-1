from __future__ import annotations

from typing import Dict, List
from urllib.parse import quote_plus, urlparse

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper


SEARCH_URL = "https://www.bing.com/search?q={query}"


class DiscoveryScraper(BaseScraper):

    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:

        url = SEARCH_URL.format(query=quote_plus(query))

        html = await self.request_manager.get_text(url)

        soup = BeautifulSoup(html, "lxml")

        records: List[Dict[str, str]] = []

        for a in soup.select("li.b_algo h2 a"):

            href = a.get("href")

            if not href:
                continue

            domain = urlparse(href).netloc

            if "bing.com" in domain:
                continue

            record = self.build_record(
                company_name=href,
                website=href,
                description=f"Discovered via search query: {query}",
                source="discovery",
                additional_info="Search engine discovery",
            )

            records.append(record)

        return records