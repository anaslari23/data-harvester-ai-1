from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List, Optional

import httpx

from utils.request_manager import RequestManager


class MCADirectScraper:
    """Scrape company data from MCA21 government portal."""

    MCA_SEARCH_URL = "https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do"

    def __init__(self, request_manager: Optional[RequestManager] = None):
        self.request_manager = request_manager or RequestManager()

    async def search_company(self, name: str) -> Optional[Dict[str, Any]]:
        """Search for company on MCA portal."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://www.mca.gov.in",
            "Accept": "application/json, text/plain, */*",
        }

        params = {"companyName": name, "companyType": "", "state": ""}

        try:
            async with httpx.AsyncClient(
                timeout=15.0, verify=False, follow_redirects=True
            ) as c:
                r = await c.get(self.MCA_SEARCH_URL, params=params, headers=headers)
                if r.status_code == 200:
                    return self._parse_mca_response(r.text, name)
        except Exception:
            pass

        return await self._ddg_mca_search(name)

    async def _ddg_mca_search(self, name: str) -> Optional[Dict[str, Any]]:
        """DuckDuckGo scoped to mca.gov.in for company CIN pages."""
        url = "https://html.duckduckgo.com/html/?q=site:mca.gov.in " + name.replace(
            " ", "+"
        )

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(url, headers=headers)
                if r.status_code == 200:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(r.text, "lxml")
                    for item in soup.select("div.result__body")[:3]:
                        snippet = item.get_text(" ")
                        directors = self._extract_names_from_snippet(snippet)
                        if directors:
                            return {"directors": directors, "source": "mca_ddg"}
        except Exception:
            pass

        return None

    def _parse_mca_response(
        self, html: str, search_name: str
    ) -> Optional[Dict[str, Any]]:
        """Parse MCA HTML response for company data."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        directors = []
        for row in soup.select("table tbody tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                if name and len(name) > 3:
                    directors.append(name)

        if directors:
            return {"directors": directors[:5], "source": "mca_direct"}

        return None

    def _extract_names_from_snippet(self, text: str) -> List[str]:
        """Extract Indian person names from snippets."""
        patterns = [
            r"(?:Director|DIN|Signatory)\s*:?\s*([A-Z][A-Z\s]{4,40})",
            r"([A-Z][A-Z\s]{4,30})\s+(?:Director|CEO|MD|CFO)",
        ]
        names = []
        for p in patterns:
            for m in re.finditer(p, text, re.I):
                name = m.group(1).strip().title()
                if 5 < len(name) < 50:
                    names.append(name)
        return list(set(names))[:5]


async def enrich_with_mca(company_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to enrich a record with MCA data."""
    if not company_name:
        return record

    scraper = MCADirectScraper()
    await asyncio.sleep(1.0)

    result = dict(record)
    mca_data = await scraper.search_company(company_name)

    if mca_data and mca_data.get("directors"):
        if not result.get("contact_name"):
            result["contact_name"] = mca_data["directors"][0]
            result["owner_role"] = "Director"

    return result
