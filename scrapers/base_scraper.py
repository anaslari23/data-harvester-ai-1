from __future__ import annotations

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
from utils.request_manager import RequestManager


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

        return {
            "company_name": company_name,
            "website": website,
            "email": email,
            "phone": phone,
            "address": addresses[0] if addresses else "",
            "description": description,
            "source": source,
            "additional_info": f"{source} profile: {profile_url}",
        }

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
        for selector in ("p", "article", "section"):
            node = soup.select_one(selector)
            if node:
                text = str(node.get_text(" ", strip=True))
                if text and len(text) > 20:
                    return text[:500]
        if fallback_text:
            return fallback_text[:500]
        return ""
