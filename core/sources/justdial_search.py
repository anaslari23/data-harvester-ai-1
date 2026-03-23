from __future__ import annotations

import asyncio
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from loguru import logger

from core.sources.http_utils import fetch_page
from core.sources.types import SeedURL, slugify


class JustDialSearch:
    async def get_company_urls(self, industry: str, city: str) -> list[SeedURL]:
        city_slug = slugify(city)
        industry_slug = slugify(industry)

        urls_to_try = [
            f"https://www.justdial.com/{city_slug.title()}/{industry_slug}-in-{city_slug}",
            f"https://www.justdial.com/{city_slug.title()}/{industry.replace(' ', '-')}-in-{city_slug.title()}",
            f"https://www.justdial.com/{city_slug.title()}/{industry_slug}-in-{city_slug}/nct-10462188",
            f"https://www.justdial.com/{city_slug.title()}/{industry_slug}",
        ]

        for url in urls_to_try:
            result = await fetch_page(url)
            if not result.success:
                continue

            companies = self._parse_justdial_listing(result.html)
            if companies:
                logger.info(f"justdial_search_done: found={len(companies)} url={url}")
                return companies
            await asyncio.sleep(2.0)

        return []

    def _parse_justdial_listing(self, html: str) -> list[SeedURL]:
        soup = BeautifulSoup(html, "lxml")
        seeds: list[SeedURL] = []

        card_selectors = [
            ".jdCard",
            ".resultbox",
            "[class*='resultcard']",
            ".store-details",
            "li.cntanr",
            ".restrocard",
            "[class*='tabcontent'] li",
            ".mr2 .store-details",
        ]

        cards = []
        for selector in card_selectors:
            cards = soup.select(selector)
            if cards:
                break

        for card in cards:
            name_el = card.select_one(
                ".jdTitle, .title, h2.title, .store-name, .fn.org, "
                "span.jcn a, .resultbox_title_anchor, .store-name a"
            )
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) < 3:
                continue

            website: str | None = None
            for a in card.select("a[href]"):
                href = a.get("href", "")
                if href.startswith("http") and "justdial" not in href:
                    website = href
                    break

            profile_url = ""
            profile_link = name_el.find_parent("a")
            if profile_link:
                href = profile_link.get("href", "")
                if href:
                    profile_url = (
                        "https://www.justdial.com" + href
                        if href.startswith("/")
                        else href
                    )

            if profile_url:
                seeds.append(
                    SeedURL(
                        url=profile_url,
                        source_name="justdial_listing",
                        expected_type="company",
                        confidence=0.75,
                    )
                )

            if website:
                seeds.append(
                    SeedURL(
                        url=website,
                        source_name="justdial_website",
                        expected_type="company",
                        confidence=0.80,
                    )
                )

        return seeds
