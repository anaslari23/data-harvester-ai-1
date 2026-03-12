@echo off

echo ======================================
echo Fixing Scraper Environment (Windows)
echo ======================================

echo.
echo Installing Python dependencies...

pip install --upgrade pip

pip install playwright aiohttp requests beautifulsoup4 lxml fake-useragent tenacity pandas

echo.
echo Installing Playwright browsers...

python -m playwright install

echo.
echo Creating utils folder if missing...

if not exist utils mkdir utils

echo.
echo Creating browser manager...

(
echo from playwright.async_api import async_playwright
echo.
echo class BrowserManager:
echo.
echo     async def fetch(self, url):
echo.
echo         async with async_playwright() as p:
echo.
echo             browser = await p.chromium.launch(headless=True)
echo.
echo             page = await browser.new_page()
echo.
echo             await page.goto(url, timeout=60000)
echo.
echo             html = await page.content()
echo.
echo             await browser.close()
echo.
echo             return html
) > utils\browser_manager.py


echo.
echo Patching request manager...

(
echo import aiohttp
echo from utils.browser_manager import BrowserManager
echo.
echo class RequestManager:
echo.
echo     def __init__(self):
echo         self.browser = BrowserManager()
echo.
echo     async def fetch(self, url):
echo.
echo         try:
echo             html = await self.browser.fetch(url)
echo             return html
echo.
echo         except Exception:
echo.
echo             async with aiohttp.ClientSession() as session:
echo                 async with session.get(url) as resp:
echo                     return await resp.text()
) > utils\request_manager.py


echo.
echo Creating HTML extraction helper...

if not exist scrapers mkdir scrapers

(
echo from bs4 import BeautifulSoup
echo import re
echo.
echo EMAIL_REGEX = r"[A-Za-z0-9._%%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
echo PHONE_REGEX = r"(\+?\d[\d\s\-]{7,}\d)"
echo.
echo def extract_emails(text):
echo     return list(set(re.findall(EMAIL_REGEX, text)))
echo.
echo def extract_phones(text):
echo     return list(set(re.findall(PHONE_REGEX, text)))
echo.
echo def parse_html(html):
echo.
echo     soup = BeautifulSoup(html, "lxml")
echo.
echo     text = soup.get_text()
echo.
echo     emails = extract_emails(text)
echo.
echo     phones = extract_phones(text)
echo.
echo     title = soup.title.text if soup.title else ""
echo.
echo     return {
echo         "title": title,
echo         "emails": emails,
echo         "phones": phones
echo     }
) > scrapers\html_utils.py


echo.
echo Creating test scraper...

(
echo import asyncio
echo from utils.request_manager import RequestManager
echo from scrapers.html_utils import parse_html
echo.
echo async def test():
echo.
echo     rm = RequestManager()
echo.
echo     url = "https://example.com"
echo.
echo     html = await rm.fetch(url)
echo.
echo     data = parse_html(html)
echo.
echo     print("Title:", data["title"])
echo     print("Emails:", data["emails"])
echo     print("Phones:", data["phones"])
echo.
echo asyncio.run(test())
) > test_scrape.py


echo.
echo Creating folders...

if not exist output mkdir output
if not exist logs mkdir logs

echo.
echo ======================================
echo Setup Complete
echo ======================================
echo.
echo Run the test with:
echo.
echo python test_scrape.py
echo.
pause