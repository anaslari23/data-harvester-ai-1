import os
import re
from typing import Dict, List
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from extractors.email_extractor import extract_best_email
from extractors.phone_extractor import extract_best_phone
from extractors.company_extractor import (
    extract_company_names_from_text,
    extract_best_company_name,
)
from scrapers.base_scraper import BaseScraper
from utils.firecrawl_client import FirecrawlClient


class DirectWebsiteScraper(BaseScraper):
    async def search_and_extract(self, query: str) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            return results

        urls = self._extract_urls_from_query(query)
        firecrawl = FirecrawlClient(api_key)

        for url in urls[:5]:
            try:
                content = firecrawl.scrape(url)
                if not content:
                    continue

                website_domain = self._extract_domain(url)
                email = extract_best_email(content, website_domain)
                phone = extract_best_phone(content)

                soup = BeautifulSoup(content, "lxml")
                text = str(soup.get_text(" ", strip=True))

                company_candidates = extract_company_names_from_text(
                    text, website_domain, max_results=5
                )
                company_name = extract_best_company_name(
                    [c[0] for c in company_candidates], website_domain
                )

                description = text[:500] if text else ""

                record = self.build_record(
                    company_name=company_name,
                    website=url,
                    email=email,
                    phone=phone,
                    description=description,
                    source="direct_website",
                    additional_info=f"Direct website scrape for: {query}",
                )
                results.append(record)

            except Exception as e:
                continue

        return results

    def _extract_urls_from_query(self, query: str) -> List[str]:
        urls = []

        urls_from_query = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', query)
        if urls_from_query:
            return [u.rstrip(".,;:") for u in urls_from_query[:5]]

        company_name = re.sub(r"[^\w\s]", " ", query).strip()

        search_patterns = [
            f"https://{company_name.replace(' ', '')}.com",
            f"https://www.{company_name.replace(' ', '')}.com",
            f"https://{company_name.replace(' ', '-').lower()}.com",
            f"https://www.{company_name.replace(' ', '-').lower()}.com",
        ]

        for url in search_patterns:
            if url not in urls:
                urls.append(url)

        return urls

    def _extract_domain(self, url: str) -> str:
        if not url:
            return ""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace("www.", "")
        except Exception:
            return ""
