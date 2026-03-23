from __future__ import annotations

import asyncio
import re
from typing import Dict, List, Optional

from utils.request_manager import RequestManager


ERP_JOB_KEYWORDS = {
    "SAP S/4HANA": ["S/4HANA", "SAP S4", "Fiori", "HANA"],
    "SAP Business One": ["SAP B1", "SAP Business One", "SAP BO"],
    "SAP": [
        "SAP MM",
        "SAP SD",
        "SAP FI",
        "SAP HR",
        "SAP ABAP",
        "SAP ECC",
        "SAP WM",
        "SAP PP",
    ],
    "Oracle": [
        "Oracle EBS",
        "Oracle Fusion",
        "Oracle Apps",
        "JD Edwards",
        "PeopleSoft",
    ],
    "Oracle NetSuite": ["NetSuite", "Netsuite"],
    "Microsoft Dynamics": [
        "Dynamics 365",
        "Dynamics AX",
        "Dynamics NAV",
        "Business Central",
        "D365",
        "MSCRM",
    ],
    "Tally": ["TallyPrime", "Tally ERP", "Tally 9"],
    "Zoho": ["Zoho Books", "Zoho CRM", "Zoho ERP"],
    "Odoo": ["Odoo", "OpenERP"],
    "Busy": ["BUSY Software", "BUSY Accounting"],
    "Marg ERP": ["MARG ERP", "Marg Software"],
    "Infor": ["Infor ERP", "Infor LN", "Infor M3"],
    "Epicor": ["Epicor ERP", "Epicor"],
}


class NaukriERPDetector:
    """Detect ERP from Naukri job postings."""

    def __init__(self, request_manager: Optional[RequestManager] = None):
        self.request_manager = request_manager or RequestManager()

    async def _fetch_ddg(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, str]]:
        """Search via DuckDuckGo for Naukri job posts."""
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
        }

        try:
            async with self.request_manager._session.get(
                url, headers=headers, timeout=15
            ) as resp:
                if resp.status == 200:
                    from bs4 import BeautifulSoup

                    html = await resp.text()
                    soup = BeautifulSoup(html, "lxml")
                    results = []
                    for item in soup.select("div.result__body")[:max_results]:
                        title = item.select_one("a.result__a")
                        if title:
                            results.append(
                                {
                                    "title": title.get_text(strip=True),
                                    "url": title.get("href", ""),
                                }
                            )
                    return results
        except Exception:
            pass
        return []

    async def detect_erp(self, company_name: str) -> Optional[str]:
        """Detect ERP from Naukri job posts."""
        if not company_name:
            return None

        query = f'site:naukri.com "{company_name}" ERP SAP Oracle Tally'

        await asyncio.sleep(1.0)

        results = await self._fetch_ddg(query)

        if not results:
            return None

        combined_text = " ".join(r.get("title", "") for r in results).upper()

        scores: Dict[str, int] = {}
        for erp, keywords in ERP_JOB_KEYWORDS.items():
            score = sum(combined_text.count(kw.upper()) for kw in keywords)
            if score > 0:
                scores[erp] = score

        if not scores:
            return None

        return max(scores, key=lambda k: scores[k])


async def detect_erp(company_name: str) -> Optional[str]:
    """Convenience function to detect ERP."""
    detector = NaukriERPDetector()
    return await detector.detect_erp(company_name)
