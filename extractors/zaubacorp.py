from __future__ import annotations

import asyncio
import re
import urllib.parse
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from utils.request_manager import RequestManager


class ZaubacorpScraper:
    """Scrape company directors from Zaubacorp.com (free MCA data)."""

    BASE = "https://www.zaubacorp.com"

    def __init__(self, request_manager: Optional[RequestManager] = None):
        self.request_manager = request_manager or RequestManager()
        self._session = None

    async def _fetch(self, url: str) -> Optional[str]:
        """Fetch a page with proper headers."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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

    async def search_company(self, company_name: str) -> List[Dict[str, Any]]:
        """Search by company name, return list of matches with CIN."""
        slug = company_name.lower().replace(" ", "-")
        slug = re.sub(r"[^a-z0-9-]", "", slug)
        url = f"{self.BASE}/company-list/p-1/company-name-{slug}/company.html"

        html = await self._fetch(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        companies = []

        for row in soup.select("table tbody tr"):
            cells = row.find_all("td")
            if len(cells) >= 3:
                name_link = cells[0].find("a")
                companies.append(
                    {
                        "name": cells[0].get_text(strip=True),
                        "cin": cells[1].get_text(strip=True),
                        "url": self.BASE + name_link["href"]
                        if name_link and name_link.get("href")
                        else "",
                        "status": cells[2].get_text(strip=True),
                    }
                )

        return companies

    async def get_directors(self, company_url: str) -> tuple[List[Dict[str, str]], str]:
        """Fetch company detail page, extract director names."""
        html = await self._fetch(company_url)
        if not html:
            return [], ""

        soup = BeautifulSoup(html, "lxml")
        directors = []

        for row in soup.select("table tbody tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                if name and len(name) > 2:
                    directors.append(
                        {
                            "name": name,
                            "designation": cells[2].get_text(strip=True)
                            if len(cells) > 2
                            else "Director",
                        }
                    )

        addr_el = soup.select_one(".registered-address, #reg-address, address")
        registered_address = addr_el.get_text(strip=True) if addr_el else ""

        return directors, registered_address

    async def enrich_company(
        self, company_name: str, existing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search and extract directors for a company."""
        result = dict(existing_data)

        if not company_name:
            return result

        await asyncio.sleep(1.5)

        companies = await self.search_company(company_name)
        if not companies:
            return result

        best = companies[0]
        for c in companies:
            if "active" in c.get("status", "").lower():
                best = c
                break

        if not best.get("url"):
            return result

        await asyncio.sleep(1.5)

        directors, reg_address = await self.get_directors(best["url"])

        if directors and not result.get("contact_name"):
            result["contact_name"] = directors[0].get("name", "")
            result["owner_role"] = directors[0].get("designation", "Director")
            result["additional_directors"] = "; ".join(
                d.get("name", "") for d in directors[:5]
            )

        if reg_address and not result.get("address"):
            result["address"] = reg_address

        return result


async def enrich_with_zaubacorp(
    company_name: str, record: Dict[str, Any]
) -> Dict[str, Any]:
    """Convenience function to enrich a record with Zaubacorp data."""
    scraper = ZaubacorpScraper()
    return await scraper.enrich_company(company_name, record)
