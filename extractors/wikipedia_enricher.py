from __future__ import annotations

import re
import urllib.parse
from typing import Any, Dict, Optional

import httpx


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


class WikipediaEnricher:
    """Enrich company data from Wikipedia API."""

    API = "https://en.wikipedia.org/api/rest_v1"
    SEARCH = "https://en.wikipedia.org/w/api.php"

    async def enrich(self, company_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich company data from Wikipedia."""
        result = dict(data)

        if not company_name:
            return result

        missing = sum(
            1
            for f in [
                result.get("contact_name"),
                result.get("turnover"),
                result.get("employee_count"),
                result.get("industry_type"),
            ]
            if not f
        )

        if missing < 1:
            return result

        page = await self._search_page(company_name)
        if not page:
            return result

        summary = await self._get_summary(page)
        if summary:
            if not result.get("company_name") and summary.get("title"):
                result["company_name"] = summary["title"]

            if not result.get("description") and summary.get("extract"):
                result["description"] = summary["extract"][:500]

            if not result.get("contact_name"):
                owner = self._extract_owner_from_summary(summary.get("extract", ""))
                if owner:
                    result["contact_name"] = owner
                    result["owner_role"] = "CEO"

        infobox = await self._get_infobox(page)
        if infobox:
            if not result.get("employee_count") and infobox.get("employee_count"):
                result["employee_count"] = infobox["employee_count"]

            if not result.get("turnover") and infobox.get("annual_turnover"):
                result["turnover"] = infobox["annual_turnover"]

            if not result.get("industry_type") and infobox.get("industry_hint"):
                result["industry_type"] = infobox["industry_hint"]

        return result

    async def _search_page(self, name: str) -> Optional[str]:
        """Search for company page on Wikipedia."""
        async with httpx.AsyncClient(timeout=10.0) as c:
            try:
                r = await c.get(
                    self.SEARCH,
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": f"{name} company India",
                        "format": "json",
                        "srlimit": 5,
                    },
                )
                results = r.json().get("query", {}).get("search", [])
                for res in results:
                    title = res.get("title", "")
                    if any(
                        w in title
                        for w in [
                            "Limited",
                            "Ltd",
                            "Inc",
                            "Corp",
                            "Industries",
                            "Technologies",
                        ]
                    ):
                        return title
                return results[0]["title"] if results else None
            except Exception:
                pass
        return None

    async def _get_summary(self, page_title: str) -> Optional[Dict[str, Any]]:
        """Get Wikipedia summary."""
        async with httpx.AsyncClient(timeout=10.0) as c:
            try:
                r = await c.get(
                    f"{self.API}/page/summary/{urllib.parse.quote(page_title)}"
                )
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
        return None

    async def _get_infobox(self, page_title: str) -> Dict[str, Any]:
        """Fetch infobox data via Wikidata API."""
        result = {}

        async with httpx.AsyncClient(timeout=10.0) as c:
            try:
                r = await c.get(
                    self.SEARCH,
                    params={
                        "action": "query",
                        "titles": page_title,
                        "prop": "pageprops",
                        "format": "json",
                    },
                )
                pages = r.json().get("query", {}).get("pages", {})
                wikidata_id = None
                for p in pages.values():
                    wikidata_id = p.get("pageprops", {}).get("wikibase_item")
                    if wikidata_id:
                        break

                if not wikidata_id:
                    return result

                wd = await c.get(
                    f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"
                )
                return self._parse_wikidata(wd.json(), wikidata_id)
            except Exception:
                pass

        return result

    def _parse_wikidata(self, data: dict, entity_id: str) -> Dict[str, Any]:
        """Parse Wikidata for company data."""
        result = {}
        entity = data.get("entities", {}).get(entity_id, {})
        claims = entity.get("claims", {})

        if "P1128" in claims:
            val = (
                claims["P1128"][0]
                .get("mainsnak", {})
                .get("datavalue", {})
                .get("value", {})
            )
            n = val.get("amount", "").lstrip("+")
            if n.isdigit():
                result["employee_count"] = _to_band(int(n))

        if "P2139" in claims:
            val = (
                claims["P2139"][0]
                .get("mainsnak", {})
                .get("datavalue", {})
                .get("value", {})
            )
            amount = val.get("amount", "").lstrip("+")
            if amount:
                try:
                    n = float(amount)
                    if n > 10000000:
                        crore = round(n / 10000000)
                        result["annual_turnover"] = f"₹{crore} Cr"
                except ValueError:
                    pass

        if "P452" in claims:
            result["industry_hint"] = "Manufacturing"

        return result

    def _extract_owner_from_summary(self, text: str) -> Optional[str]:
        """Extract CEO/founder name from summary text."""
        if not text:
            return None

        patterns = [
            r"(?:led by|CEO is|headed by|MD is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s+(?:is|serves as)\s+(?:the\s+)?(?:CEO|MD|Chairman)",
            r"founded by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1)
        return None


async def enrich_with_wikipedia(
    company_name: str, record: Dict[str, Any]
) -> Dict[str, Any]:
    """Convenience function to enrich a record with Wikipedia data."""
    enricher = WikipediaEnricher()
    return await enricher.enrich(company_name, record)
