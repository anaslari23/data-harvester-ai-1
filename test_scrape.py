import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from utils.request_manager import RequestManager
from scrapers.html_utils import parse_html

async def test():
    rm = RequestManager()
    url = "https://primacyinfotech.com"
    print(f"Fetching {url} using Playwright...")
    html = await rm.fetch(url)
    data = parse_html(html)
    print("Page Title:", data["title"])
    print("Emails:", data["emails"])
    print("Phones:", data["phones"])

if __name__ == "__main__":
    # Playwright requires a specific event loop policy on Windows sometimes, 
    # but asyncio.run is usually fine for a quick script
    asyncio.run(test())
