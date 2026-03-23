from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup


def _to_band(n: int) -> str:
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


class TradeIndiaProfileScraper:
    """Scrape TradeIndia company profile pages for owner/turnover."""

    async def enrich_from_profile(
        self, company_name: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich company data from TradeIndia profile."""
        result = dict(data)

        if not company_name:
            return result

        profile_url = await self._find_profile_url(company_name, result.get("city", ""))

        if not profile_url:
            return result

        await asyncio.sleep(1.0)

        html = await self._fetch_page(profile_url)
        if not html or len(html) < 500:
            return result

        return self._parse_profile(html, profile_url, result)

    async def _find_profile_url(
        self, company_name: str, city: str = ""
    ) -> Optional[str]:
        """Search DDG for TradeIndia profile URL."""
        query = f'site:tradeindia.com "{company_name}" {city} company profile'

        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(url, headers=headers)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "lxml")
                    for item in soup.select("div.result__body")[:5]:
                        link = item.select_one("a.result__a, a.result__url")
                        if not link:
                            continue
                        href = link.get("href", "")
                        if "tradeindia.com" in href:
                            if "/products/" not in href and "/seller/" not in href:
                                if href.count("/") <= 5:
                                    return href
        except Exception:
            pass

        return None

    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as c:
                r = await c.get(url, headers=headers)
                if r.status_code == 200:
                    return r.text
        except Exception:
            pass

        return None

    def _parse_profile(
        self, html: str, url: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = dict(data)
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator=" ")

        if not result.get("contact_name"):
            contact_patterns = [
                r"Contact\s+Person\s*:?\s*(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*"
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
                r"Owner\s*:?\s*(?:Mr\.?|Mrs\.?|Ms\.?)?\s*"
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
                r"Managing\s+Director\s*:?\s*"
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
                r"Key\s+Contact\s*:?\s*(?:Mr\.?|Mrs\.?|Ms\.?)?\s*"
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
            ]
            for pattern in contact_patterns:
                m = re.search(pattern, text, re.I)
                if m:
                    name = m.group(1).strip()
                    if 4 < len(name) < 50:
                        result["contact_name"] = name
                        if "Managing Director" in pattern:
                            result["owner_role"] = "Managing Director"
                        elif "Owner" in pattern:
                            result["owner_role"] = "Owner"
                        else:
                            result["owner_role"] = "Contact Person"
                        break

        if not result.get("contact_name"):
            for el in soup.select(
                ".contact-name, .contact-person, .cp-name, "
                "[class*='contact'] strong, [class*='owner'], .name"
            ):
                name = el.get_text(strip=True)
                if 4 < len(name) < 50 and re.match(r"[A-Z][a-z]", name):
                    result["contact_name"] = name
                    result["owner_role"] = "Contact Person"
                    break

        if not result.get("turnover"):
            turnover_patterns = [
                r"Annual\s+Turnover\s*:?\s*"
                r"(Rs\.?\s*[\d.,]+\s*(?:Lakh|Crore|Cr|L)[^<\n]{0,40})",
                r"Turnover\s*(?:Rs\.?|₹)?:?\s*"
                r"((?:Rs\.?|₹)\s*[\d.,]+\s*(?:Lakh|Crore|Cr)[^<\n]{0,30})",
                r"Sales\s+Turnover\s*:?\s*"
                r"(Rs\.?\s*[\d.,]+\s*(?:Lakh|Crore|Cr)[^<\n]{0,30})",
            ]
            for pattern in turnover_patterns:
                m = re.search(pattern, text, re.I)
                if m:
                    raw = m.group(1).strip()
                    result["turnover"] = self._normalize_turnover(raw)
                    break

        if not result.get("employee_count"):
            emp_m = re.search(
                r"(?:No\.\s+of\s+(?:Employees?|Staff)|Employees?|Staff|"
                r"Team\s+Size)\s*:?\s*"
                r"([\d,]+\s*[-–to]*\s*[\d,]*\+?)",
                text,
                re.I,
            )
            if emp_m:
                n_m = re.search(r"[\d,]+", emp_m.group(1))
                if n_m:
                    try:
                        n = int(n_m.group().replace(",", ""))
                        if 1 <= n <= 500000:
                            result["employee_count"] = _to_band(n)
                    except ValueError:
                        pass

        if not result.get("industry_type"):
            nature_m = re.search(
                r"Nature\s+of\s+(?:Business|Company)\s*:?\s*([A-Za-z\s/&]+?)(?:\n|<)",
                text,
                re.I,
            )
            if nature_m:
                result["industry_type"] = nature_m.group(1).strip()

        if not result.get("address"):
            addr_m = re.search(
                r"(?:Address|Location)\s*:?\s*([^\n]{10,150})",
                text,
                re.I,
            )
            if addr_m:
                result["address"] = addr_m.group(1).strip()

        gst_m = re.search(
            r"GST\s*(?:No\.?|Number|IN)?\s*:?\s*"
            r"([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
            text,
            re.I,
        )
        if gst_m:
            existing = result.get("additional_info", "")
            gst_num = gst_m.group(1)
            if existing:
                result["additional_info"] = f"{existing} | GST: {gst_num}"
            else:
                result["additional_info"] = f"GST: {gst_num}"

        return result

    def _normalize_turnover(self, raw: str) -> str:
        raw = raw.strip()
        crore_m = re.search(r"([\d.]+)\s*(?:Crore|Cr)", raw, re.I)
        lakh_m = re.search(r"([\d.]+)\s*Lakh", raw, re.I)

        if crore_m:
            return f"₹{crore_m.group(1)} Cr"
        if lakh_m:
            val = float(lakh_m.group(1))
            return f"₹{val / 100:.2f} Cr"
        return raw


async def enrich_with_tradeindia(
    company_name: str, record: Dict[str, Any]
) -> Dict[str, Any]:
    """Convenience function."""
    scraper = TradeIndiaProfileScraper()
    return await scraper.enrich_from_profile(company_name, record)
