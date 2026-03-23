from __future__ import annotations

import asyncio
import re
import urllib.parse
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup

from utils.request_manager import RequestManager


class ToflerScraper:
    """Scrape company financials from Tofler.in (free MCA data)."""

    BASE = "https://www.tofler.in"

    def __init__(self, request_manager: Optional[RequestManager] = None):
        self.request_manager = request_manager or RequestManager()

    async def _fetch(self, url: str) -> Optional[str]:
        """Fetch a page."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            async with self.request_manager._session.get(
                url, headers=headers, timeout=15
            ) as resp:
                if resp.status == 200:
                    return await resp.text()
        except Exception:
            pass
        return None

    def _to_band(self, n: int) -> str:
        """Convert number to employee band."""
        if n <= 10:
            return "1-10"
        if n <= 50:
            return "11-50"
        if n <= 200:
            return "51-200"
        if n <= 500:
            return "201-500"
        if n <= 1000:
            return "501-1000"
        return "1000+"

    async def search_and_enrich(
        self, company_name: str, existing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search company and extract turnover + employee count."""
        result = dict(existing_data)

        if not company_name:
            return result

        search_url = (
            f"{self.BASE}/search?search_text={urllib.parse.quote(company_name)}"
        )

        await asyncio.sleep(1.5)

        html = await self._fetch(search_url)
        if not html:
            return result

        soup = BeautifulSoup(html, "lxml")

        first_link = soup.select_one(
            ".company-name a, .search-result a, table tbody tr td a"
        )
        if not first_link:
            return result

        company_url = self.BASE + first_link.get("href", "")
        if not company_url:
            return result

        await asyncio.sleep(1.5)

        detail_html = await self._fetch(company_url)
        if not detail_html:
            return result

        dsoup = BeautifulSoup(detail_html, "lxml")
        text = dsoup.get_text(separator=" ")

        if not result.get("turnover"):
            turnover_patterns = [
                r"(?:turnover|revenue|sales)\s*:?\s*"
                r"(?:Rs\.?|₹|INR)?\s*([\d,.]+)\s*(?:crore|cr|lakh|million|billion)",
                r"(?:Rs\.?|₹)\s*([\d,.]+)\s*(?:cr(?:ore)?)",
            ]
            for p in turnover_patterns:
                m = re.search(p, text, re.I)
                if m:
                    result["turnover"] = f"₹{m.group(1)} {m.group(2).title()}"
                    break

        if not result.get("employee_count"):
            emp_m = re.search(
                r"(?:employees?|headcount|workforce)\s*:?\s*([\d,]+)", text, re.I
            )
            if emp_m:
                try:
                    n = int(emp_m.group(1).replace(",", ""))
                    if 1 <= n <= 500000:
                        result["employee_count"] = self._to_band(n)
                except ValueError:
                    pass

        return result


async def enrich_with_tofler(
    company_name: str, record: Dict[str, Any]
) -> Dict[str, Any]:
    """Convenience function to enrich a record with Tofler data."""
    scraper = ToflerScraper()
    return await scraper.search_and_enrich(company_name, record)
