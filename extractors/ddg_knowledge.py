from __future__ import annotations

import re
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


class DDGKnowledgePanel:
    """Enrich company data from DuckDuckGo knowledge panel."""

    async def lookup(self, company_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Lookup company on DuckDuckGo."""
        result = dict(data)

        if not company_name:
            return result

        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": company_name,
                        "format": "json",
                        "no_redirect": "1",
                        "skip_disambig": "1",
                    },
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if r.status_code != 200:
                    return result

                panel = r.json()
        except Exception:
            return result

        heading = panel.get("Heading", "")
        if heading and not result.get("company_name"):
            result["company_name"] = heading

        abstract = panel.get("AbstractText", "")
        if abstract and not result.get("description"):
            result["description"] = abstract[:500]

        infobox = panel.get("Infobox", {})
        if infobox and isinstance(infobox, dict):
            for item in infobox.get("content", []):
                if not isinstance(item, dict):
                    continue
                label = item.get("label", "").lower()
                value = item.get("value", "")

                if not value:
                    continue

                if not isinstance(value, str):
                    continue

                if "ceo" in label or "chief executive" in label:
                    if not result.get("contact_name"):
                        result["contact_name"] = value
                        result["owner_role"] = "CEO"

                elif "founder" in label:
                    if not result.get("contact_name"):
                        result["contact_name"] = value
                        result["owner_role"] = "Founder"

                elif "employee" in label:
                    if not result.get("employee_count"):
                        n = re.search(r"[\d,]+", value)
                        if n:
                            try:
                                result["employee_count"] = _to_band(
                                    int(n.group().replace(",", ""))
                                )
                            except ValueError:
                                pass

                elif "revenue" in label or "turnover" in label:
                    if not result.get("turnover"):
                        result["turnover"] = value

                elif "industry" in label:
                    if not result.get("industry_type"):
                        result["industry_type"] = value

                elif "headquarters" in label or (
                    isinstance(value, str) and "headquarters" in value.lower()
                ):
                    if not result.get("address"):
                        result["address"] = value

        related = panel.get("RelatedTopics", [])
        if related and isinstance(related, list):
            for topic in related[:3]:
                if isinstance(topic, dict):
                    text = topic.get("Text", "")
                    if not result.get("description") and len(text) > 20:
                        result["description"] = text[:300]

        return result


async def enrich_with_ddg(company_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to enrich a record with DDG data."""
    panel = DDGKnowledgePanel()
    return await panel.lookup(company_name, record)
