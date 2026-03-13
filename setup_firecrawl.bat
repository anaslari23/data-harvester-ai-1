@echo off
echo ======================================
echo Firecrawl Setup (Stable Version)
echo ======================================

echo Installing dependencies...
pip install firecrawl-py beautifulsoup4 lxml requests

echo.

REM Create folders if missing
if not exist utils mkdir utils
if not exist extractors mkdir extractors
if not exist scrapers mkdir scrapers

echo.

echo Creating Firecrawl client...

echo from firecrawl import FirecrawlApp> utils\firecrawl_client.py
echo.>> utils\firecrawl_client.py
echo class FirecrawlClient:>> utils\firecrawl_client.py
echo.>> utils\firecrawl_client.py
echo     def __init__(self, api_key):>> utils\firecrawl_client.py
echo         self.app = FirecrawlApp(api_key=api_key)>> utils\firecrawl_client.py
echo.>> utils\firecrawl_client.py
echo     def scrape(self, url):>> utils\firecrawl_client.py
echo         try:>> utils\firecrawl_client.py
echo             result = self.app.scrape_url(url, formats=["markdown"])>> utils\firecrawl_client.py
echo             return result.get("markdown", "")>> utils\firecrawl_client.py
echo         except Exception as e:>> utils\firecrawl_client.py
echo             print("Firecrawl error:", e)>> utils\firecrawl_client.py
echo             return "">> utils\firecrawl_client.py

echo.

echo Creating company extractor...

echo import re> extractors\company_extractor.py
echo.>> extractors\company_extractor.py
echo EMAIL_REGEX = r"[A-Za-z0-9._%%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}">> extractors\company_extractor.py
echo PHONE_REGEX = r"\+?\d[\d\s\-]{7,}\d">> extractors\company_extractor.py
echo.>> extractors\company_extractor.py
echo def parse_company_page(text, website):>> extractors\company_extractor.py
echo.>> extractors\company_extractor.py
echo     emails = list(set(re.findall(EMAIL_REGEX, text)))>> extractors\company_extractor.py
echo     phones = list(set(re.findall(PHONE_REGEX, text)))>> extractors\company_extractor.py
echo.>> extractors\company_extractor.py
echo     return {>> extractors\company_extractor.py
echo         "Company Name": website,>> extractors\company_extractor.py
echo         "Website": website,>> extractors\company_extractor.py
echo         "Phone Number": ", ".join(phones[:3]),>> extractors\company_extractor.py
echo         "EMail Address": ", ".join(emails[:3])>> extractors\company_extractor.py
echo     }>> extractors\company_extractor.py

echo.

echo Creating website scraper...

echo from extractors.company_extractor import parse_company_page> scrapers\website_scraper.py
echo from scrapers.base_scraper import BaseScraper>> scrapers\website_scraper.py
echo from utils.firecrawl_client import FirecrawlClient>> scrapers\website_scraper.py
echo import os>> scrapers\website_scraper.py
echo.>> scrapers\website_scraper.py
echo class WebsiteScraper(BaseScraper):>> scrapers\website_scraper.py
echo.>> scrapers\website_scraper.py
echo     async def search_and_extract(self, query):>> scrapers\website_scraper.py
echo.>> scrapers\website_scraper.py
echo         if not query.startswith("http"):>> scrapers\website_scraper.py
echo             return []>> scrapers\website_scraper.py
echo.>> scrapers\website_scraper.py
echo         api_key = os.getenv("FIRECRAWL_API_KEY")>> scrapers\website_scraper.py
echo.>> scrapers\website_scraper.py
echo         firecrawl = FirecrawlClient(api_key)>> scrapers\website_scraper.py
echo.>> scrapers\website_scraper.py
echo         content = firecrawl.scrape(query)>> scrapers\website_scraper.py
echo.>> scrapers\website_scraper.py
echo         if not content:>> scrapers\website_scraper.py
echo             return []>> scrapers\website_scraper.py
echo.>> scrapers\website_scraper.py
echo         company = parse_company_page(content, query)>> scrapers\website_scraper.py
echo.>> scrapers\website_scraper.py
echo         return [company]>> scrapers\website_scraper.py

echo.

echo ======================================
echo Setup Complete
echo ======================================

pause