from extractors.company_extractor import parse_company_page
from scrapers.base_scraper import BaseScraper
from utils.firecrawl_client import FirecrawlClient
import os

class WebsiteScraper(BaseScraper):

    async def search_and_extract(self, query):

        if not query.startswith("http"):
            return []

        api_key = os.getenv("FIRECRAWL_API_KEY")

        firecrawl = FirecrawlClient(api_key)

        content = firecrawl.scrape(query)

        if not content:
            return []

        company = parse_company_page(content, query)

        return [company]
