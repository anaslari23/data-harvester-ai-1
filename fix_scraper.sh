#!/usr/bin/env bash

set -e

echo "======================================"
echo "Fixing Scraper Environment"
echo "======================================"

PROJECT_ROOT=$(pwd)

echo "Project root: $PROJECT_ROOT"


echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip

pip install \
playwright \
aiohttp \
requests \
beautifulsoup4 \
lxml \
fake-useragent \
tenacity \
pandas


echo ""
echo "Installing Playwright browsers..."
python -m playwright install


echo ""
echo "Creating browser manager..."

mkdir -p utils

cat << 'EOF' > utils/browser_manager.py
from playwright.async_api import async_playwright

class BrowserManager:

    async def fetch(self, url: str):

        async with async_playwright() as p:

            browser = await p.chromium.launch(headless=True)

            page = await browser.new_page()

            await page.goto(url, timeout=60000)

            html = await page.content()

            await browser.close()

            return html
EOF


echo ""
echo "Patching request manager..."

if [ -f utils/request_manager.py ]; then

cat << 'EOF' > utils/request_manager.py
import asyncio
import random
import aiohttp
from utils.browser_manager import BrowserManager

class RequestManager:

    def __init__(self):

        self.browser = BrowserManager()

    async def fetch(self, url):

        try:
            html = await self.browser.fetch(url)
            return html
        except Exception:

            async with aiohttp.ClientSession() as session:

                async with session.get(url) as resp:

                    return await resp.text()
EOF

fi


echo ""
echo "Ensuring scrapers directory exists..."
mkdir -p scrapers


echo ""
echo "Adding robust HTML extractor helper..."

cat << 'EOF' > scrapers/html_utils.py
from bs4 import BeautifulSoup
import re

EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
PHONE_REGEX = r"(\\+?\\d[\\d\\s\\-]{7,}\\d)"

def extract_emails(text):
    return list(set(re.findall(EMAIL_REGEX, text)))

def extract_phones(text):
    return list(set(re.findall(PHONE_REGEX, text)))

def parse_html(html):

    soup = BeautifulSoup(html, "lxml")

    text = soup.get_text()

    emails = extract_emails(text)

    phones = extract_phones(text)

    title = soup.title.text if soup.title else ""

    return {
        "title": title,
        "emails": emails,
        "phones": phones,
        "text": text[:1000]
    }
EOF


echo ""
echo "Creating test scraper..."

cat << 'EOF' > test_scrape.py
import asyncio
from utils.request_manager import RequestManager
from scrapers.html_utils import parse_html

async def test():

    rm = RequestManager()

    url = "https://example.com"

    html = await rm.fetch(url)

    data = parse_html(html)

    print("Page Title:", data["title"])
    print("Emails:", data["emails"])
    print("Phones:", data["phones"])

asyncio.run(test())
EOF


echo ""
echo "Creating output folders..."

mkdir -p output
mkdir -p logs


echo ""
echo "======================================"
echo "Setup complete"
echo "======================================"
echo ""
echo "To test scraping run:"
echo ""
echo "python test_scrape.py"
echo ""
echo "If that works, your scrapers can now use"
echo "browser rendering for Google, IndiaMART, etc."
echo ""