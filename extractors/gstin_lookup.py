from __future__ import annotations

import asyncio
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


class GSTINLookup:
    """Look up company details via GSTIN (Goods and Services Tax Identification Number)."""

    VALID_GSTIN_PATTERN = re.compile(
        r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    )

    def is_valid_gstin(self, gstin: str) -> bool:
        """Check if a GSTIN is valid."""
        if not gstin:
            return False
        gstin = gstin.upper().strip()
        return bool(self.VALID_GSTIN_PATTERN.match(gstin))

    def extract_gstin_from_text(self, text: str) -> Optional[str]:
        """Extract a valid GSTIN from text."""
        matches = re.findall(
            r"([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
            text.upper(),
        )
        for match in matches:
            if self.is_valid_gstin(match):
                return match
        return None

    async def lookup_gstin(self, gstin: str) -> Optional[Dict[str, Any]]:
        """Look up GSTIN details via public API."""
        if not self.is_valid_gstin(gstin):
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(
                    f"https://commonapi.masters India.com/GstinAPI21/decodeGstin",
                    params={"gstin": gstin.upper()},
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json",
                    },
                )
                if r.status_code == 200:
                    data = r.json()
                    if data.get("success"):
                        return data.get("data", {})
        except Exception:
            pass

        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(
                    f"https://api.gstins.com/v1/details/{gstin.upper()}",
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json",
                    },
                )
                if r.status_code == 200:
                    return r.json()
        except Exception:
            pass

        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(
                    "https://gstlookup.in/api/v1/gstin",
                    params={"gstin": gstin.upper()},
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json",
                    },
                )
                if r.status_code == 200:
                    return r.json()
        except Exception:
            pass

        return None

    def parse_gstin_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GSTIN API response into standardized fields."""
        result = {}

        if not data:
            return result

        legal_name = data.get("legalName") or data.get("lgnm") or data.get("tradeName")
        if legal_name:
            result["company_name"] = legal_name

        trade_name = data.get("tradeNam") or data.get("dba")
        if trade_name and not result.get("company_name"):
            result["company_name"] = trade_name

        addr = data.get("addr") or data.get("address") or {}
        if isinstance(addr, dict):
            bno = addr.get("bno", "")
            city = addr.get("city", "")
            st = addr.get("st", "")
            district = addr.get("district", "")
            locality = addr.get("locality", "")

            parts = [locality, bno, locality and st and f"{locality}, {st}" or st]
            parts = [p for p in parts if p]

            full_addr = ", ".join(filter(None, [", ".join(parts), city, district, st]))
            if full_addr:
                result["address"] = full_addr

            if city:
                result["city"] = city
            if district:
                result["city"] = district
            if st:
                result["state"] = st

        if data.get("ctb"):
            result["constitution"] = data.get("ctb")

        if data.get("gstin"):
            result["gstin"] = data.get("gstin")

        if data.get("eibl"):
            result["additional_info"] = f"Business Type: {data.get('eibl')}"

        return result


async def enrich_with_gstin(gstin: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to enrich a record with GSTIN data."""
    result = dict(record)

    if not gstin:
        text_fields = [
            str(record.get("additional_info", "")),
            str(record.get("description", "")),
            str(record.get("address", "")),
        ]
        for field in text_fields:
            gst_m = re.search(
                r"([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
                field.upper(),
            )
            if gst_m:
                gstin = gst_m.group(1)
                break

    if not gstin:
        return result

    lookup = GSTINLookup()
    if not lookup.is_valid_gstin(gstin):
        return result

    await asyncio.sleep(0.5)

    data = await lookup.lookup_gstin(gstin)
    if not data:
        return result

    parsed = lookup.parse_gstin_response(data)

    for key, value in parsed.items():
        if key == "additional_info":
            existing = result.get("additional_info", "")
            if existing:
                result["additional_info"] = f"{existing} | {value}"
            else:
                result["additional_info"] = value
        elif key not in result or not result.get(key):
            result[key] = value

    return result
