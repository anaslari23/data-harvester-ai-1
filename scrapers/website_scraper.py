import asyncio
import os
from typing import Dict, List

from bs4 import BeautifulSoup
from extractors.email_extractor import extract_best_email
from extractors.phone_extractor import extract_best_phone
from extractors.company_extractor import (
    extract_company_names_from_text,
    extract_best_company_name,
)
from extractors.address_extractor import extract_addresses
from scrapers.base_scraper import BaseScraper
from utils.firecrawl_client import FirecrawlClient


class WebsiteScraper(BaseScraper):
    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:
        if not str(query).startswith(("http://", "https://")):
            return []

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            return []

        firecrawl = FirecrawlClient(api_key)
        content = await asyncio.to_thread(firecrawl.scrape, query)

        if not content:
            return []

        soup = BeautifulSoup(content, "lxml")
        text = str(soup.get_text(" ", strip=True))
        website_domain = self._extract_domain(query)

        emails = extract_best_email(text, website_domain)
        phones = extract_best_phone(text)
        addresses = extract_addresses(content)

        company_candidates = extract_company_names_from_text(
            text, website_domain, max_results=5
        )
        company_name = extract_best_company_name(
            [c[0] for c in company_candidates], website_domain
        )

        if not company_name:
            company_name = query

        description = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            description = str(meta.get("content", ""))
        elif text:
            description = text[:500]

        return [
            self.build_record(
                company_name=company_name,
                website=query,
                email=emails,
                phone=phones,
                address=addresses[0] if addresses else "",
                description=description,
                source="website",
                additional_info=f"Website scrape target: {query}",
            )
        ]

    def _extract_domain(self, url: str) -> str:
        from urllib.parse import urlparse

        if not url:
            return ""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace("www.", "")
        except Exception:
            return ""
