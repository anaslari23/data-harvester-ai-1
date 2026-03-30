from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from extractors.address_extractor import extract_addresses
from extractors.email_extractor import extract_best_email
from extractors.phone_extractor import extract_best_phone
from extractors.company_extractor import (
    extract_company_names_from_text,
    extract_best_company_name,
)
from extractors.decision_maker_extractor import extract_decision_makers
from extractors.structured_data_extractor import extract_structured_data
from utils.request_manager import RequestManager

# Sub-pages to crawl for richer contact/leadership data
_SECONDARY_SLUGS = [
    "/about", "/about-us", "/about_us", "/aboutus",
    "/team", "/our-team", "/leadership", "/management",
    "/contact", "/contact-us", "/contact_us", "/contactus",
    "/directors", "/board", "/founders",
]

_NAME_RE = re.compile(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})")


class BaseScraper(ABC):
    """Abstract base class for all platform scrapers."""

    def __init__(self, request_manager: RequestManager) -> None:
        self.request_manager = request_manager

    async def initialize(self) -> None:
        return None

    @abstractmethod
    async def search_and_extract(self, query: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def absolute_url(self, base_url: str, maybe_relative: str | None) -> str:
        if not maybe_relative:
            return ""
        return urljoin(base_url, maybe_relative)

    def build_record(self, **kwargs: Any) -> Dict[str, Any]:
        record: Dict[str, Any] = {
            "company_name": "",
            "website": "",
            "phone": "",
            "email": "",
            "address": "",
            "city": "",
            "state": "",
            "country": "",
            "industry": "",
            "industry_type": "",
            "description": "",
            "additional_info": "",
            "source": "",
            "employee_count": "",
            "branch_count": "",
            "turnover": "",
            "contact_name": "",
            "erp_software": "",
        }
        record.update(kwargs)
        return record

    def _extract_domain(self, url: str) -> str:
        if not url:
            return ""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace("www.", "")
        except Exception:
            return ""

    async def _fetch_secondary_pages(self, base_url: str) -> str:
        """Fetch one sub-page (about/team/contact/leadership) and return its HTML.

        Tries each candidate slug in order and returns the first successful fetch
        that has meaningful content (> 500 chars). Returns empty string if none found.
        """
        parsed = urlparse(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        for slug in _SECONDARY_SLUGS:
            url = origin + slug
            try:
                html = await self.request_manager.fetch(url)
                if html and len(html) > 500:
                    return html
            except Exception:
                continue
        return ""

    def _extract_contact_from_html(self, html: str) -> str:
        """Extract the first plausible decision-maker name from raw HTML."""
        candidates = extract_decision_makers(html)
        for entry in candidates:
            match = _NAME_RE.search(entry)
            if match:
                return match.group(1)
        return ""

    async def enrich_from_profile(
        self, profile_url: str, source: str
    ) -> Dict[str, Any]:
        if not profile_url:
            return {}

        try:
            html = await self.request_manager.fetch(profile_url)
        except Exception:
            return {}

        soup = BeautifulSoup(html, "lxml")
        text = str(soup.get_text(" ", strip=True))
        website_domain = self._extract_domain(profile_url)

        # --- primary page extractions ---
        email = extract_best_email(text, website_domain)
        phone = extract_best_phone(text)
        addresses = extract_addresses(html)
        website = self._extract_external_website(soup, profile_url)
        description = self._extract_description(soup, text)

        company_candidates = extract_company_names_from_text(
            text, website_domain, max_results=5
        )
        company_name = extract_best_company_name(
            [c[0] for c in company_candidates], website_domain
        )

        # --- JSON-LD structured data (highest fidelity) ---
        structured = extract_structured_data(html)
        contact_name = structured.get("contact_name", "")
        employee_count = structured.get("employee_count", "")
        if not email:
            email = structured.get("email", "")
        if not phone:
            phone = structured.get("phone", "")
        if not addresses and structured.get("address"):
            addresses = [structured["address"]]
        if not company_name and structured.get("company_name"):
            company_name = structured["company_name"]
        if not description and structured.get("description"):
            description = structured["description"]
        city = structured.get("city", "")
        state = structured.get("state", "")
        country = structured.get("country", "")

        # --- secondary pages (about/team/contact) for decision makers ---
        if not contact_name:
            secondary_html = await self._fetch_secondary_pages(
                website or profile_url
            )
            if secondary_html:
                # Try structured data on secondary page first
                sec_structured = extract_structured_data(secondary_html)
                contact_name = sec_structured.get("contact_name", "")

                if not contact_name:
                    contact_name = self._extract_contact_from_html(secondary_html)

                # Also fill any still-missing contact fields from secondary page
                if not email or not phone:
                    sec_soup = BeautifulSoup(secondary_html, "lxml")
                    sec_text = sec_soup.get_text(" ", strip=True)
                    if not email:
                        email = extract_best_email(sec_text, website_domain)
                    if not phone:
                        phone = extract_best_phone(sec_text)
                    if not addresses:
                        addresses = extract_addresses(secondary_html)

        # Decision makers from primary page as last resort
        if not contact_name:
            contact_name = self._extract_contact_from_html(html)

        result = {
            "company_name": company_name,
            "website": website,
            "email": email,
            "phone": phone,
            "address": addresses[0] if addresses else "",
            "description": description,
            "source": source,
            "additional_info": f"{source} profile: {profile_url}",
            "contact_name": contact_name,
            "employee_count": employee_count,
        }
        # Only include city/state/country if found
        if city:
            result["city"] = city
        if state:
            result["state"] = state
        if country:
            result["country"] = country

        return result

    def merge_records(
        self, base: Dict[str, Any], extra: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged = dict(base)
        for key, value in extra.items():
            if value and not merged.get(key):
                merged[key] = value
        if extra.get("additional_info") and base.get("additional_info"):
            merged["additional_info"] = (
                f"{base['additional_info']} | {extra['additional_info']}"
            )
        return merged

    def _extract_external_website(self, soup: BeautifulSoup, profile_url: str) -> str:
        for anchor in soup.select("a[href]"):
            href_attr = anchor.get("href")
            if isinstance(href_attr, list):
                href = str(href_attr[0]) if href_attr else ""
            else:
                href = str(href_attr or "").strip()
            if not href or href.startswith(("mailto:", "tel:", "#", "javascript:")):
                continue
            absolute = urljoin(profile_url, href)
            if (
                absolute
                and absolute != profile_url
                and not any(
                    blocked in absolute
                    for blocked in [
                        "google.",
                        "linkedin.com",
                        "indiamart.com",
                        "tradeindia.com",
                        "justdial.com",
                    ]
                )
            ):
                return absolute
        return ""

    def _extract_description(self, soup: BeautifulSoup, fallback_text: str) -> str:
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            content = meta.get("content")
            return str(content).strip() if content else ""
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return str(og_desc["content"]).strip()[:500]
        for selector in ("p", "article", "section"):
            node = soup.select_one(selector)
            if node:
                text = str(node.get_text(" ", strip=True))
                if text and len(text) > 20:
                    return text[:500]
        if fallback_text:
            return fallback_text[:500]
        return ""
