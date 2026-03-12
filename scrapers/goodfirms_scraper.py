from __future__ import annotations

from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper


GOODFIRMS_DIRECTORY = "https://www.goodfirms.co/directory/software-development-companies"


class GoodFirmsScraper(BaseScraper):

    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:

        html = await self.request_manager.get_text(GOODFIRMS_DIRECTORY)

        soup = BeautifulSoup(html, "lxml")

        records: List[Dict[str, str]] = []

        cards = soup.find_all("div", class_=True)

        print("GoodFirms cards found:", len(cards))

        for card in cards[:20]:

            name_el = card.select_one("h3 a")

            if not name_el:
                continue

            name = name_el.get_text(" ", strip=True)

            profile_url = urljoin(GOODFIRMS_DIRECTORY, name_el.get("href"))

            desc_el = card.select_one("p")

            description = desc_el.get_text(" ", strip=True) if desc_el else ""

            profile_data = await self.enrich_from_profile(profile_url, "GoodFirms")

            record = self.build_record(
                company_name=name,
                website=profile_data.get("website", ""),
                description=description,
                industry="Software Development",
                source="goodfirms",
                additional_info=f"GoodFirms directory scrape",
            )

            records.append(self.merge_records(record, profile_data))

        return records