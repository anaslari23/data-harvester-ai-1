import asyncio
import os

from extractors.company_extractor import parse_company_page
from scrapers.base_scraper import BaseScraper
from utils.firecrawl_client import FirecrawlClient


class WebsiteScraper(BaseScraper):
    async def search_and_extract(self, query):
        if not str(query).startswith(("http://", "https://")):
            return []

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            return []

        firecrawl = FirecrawlClient(api_key)
        content = await asyncio.to_thread(firecrawl.scrape, query)

        if not content:
            return []

        company = parse_company_page(content, query)

        return [
            self.build_record(
                company_name=company.get("Company Name", "") or query,
                website=company.get("Website", "") or query,
                phone=company.get("Phone Number", ""),
                email=company.get("EMail Address", ""),
                description="Extracted from company website using Firecrawl",
                source="website",
                additional_info=f"Website scrape target: {query}",
            )
        ]
