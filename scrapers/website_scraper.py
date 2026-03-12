from __future__ import annotations

from typing import Dict, List

from extractors.company_extractor import parse_company_page
from scrapers.base_scraper import BaseScraper


class WebsiteScraper(BaseScraper):

    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:

        # Only process real website URLs
        if "http://" not in query and "https://" not in query:
            return []

        html = await self.request_manager.get_text(query)

        # Use the new company extractor
        company_data = parse_company_page(
            html=html,
            url=query,
            sl_no=1
        )

        return [company_data]