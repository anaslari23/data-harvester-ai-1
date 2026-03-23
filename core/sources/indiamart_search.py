from __future__ import annotations

import asyncio
import re
import urllib.parse
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from loguru import logger

from core.sources.http_utils import fetch_page, extract_phones_from_text
from core.sources.types import SeedURL, slugify


class IndiaMartSearch:
    INDUSTRY_SLUGS = {
        "oil manufacturer": "oil-manufacturers",
        "edible oil": "edible-oil-manufacturers",
        "mustard oil": "mustard-oil-manufacturers",
        "lubricant": "lubricant-oil-manufacturers",
        "it services": "it-services",
        "software": "software-companies",
        "pharma": "pharmaceutical-companies",
        "steel": "steel-manufacturers",
        "textile": "textile-manufacturers",
        "garment": "garment-manufacturers",
        "plastic": "plastic-manufacturers",
        "chemical": "chemical-manufacturers",
        "food processing": "food-processing-companies",
        "packaging": "packaging-companies",
        "engineering": "engineering-companies",
        "electronics": "electronics-manufacturers",
        "furniture": "furniture-manufacturers",
        "construction": "construction-companies",
        "logistics": "logistics-companies",
        "hospital": "hospitals",
        "manufacturer": "manufacturers",
    }

    CITY_SLUGS = {
        "kolkata": "kolkata",
        "mumbai": "mumbai",
        "delhi": "delhi",
        "bangalore": "bangalore",
        "bengaluru": "bangalore",
        "hyderabad": "hyderabad",
        "chennai": "chennai",
        "pune": "pune",
        "ahmedabad": "ahmedabad",
        "surat": "surat",
        "jaipur": "jaipur",
        "lucknow": "lucknow",
        "kanpur": "kanpur",
        "nagpur": "nagpur",
        "jamshedpur": "jamshedpur",
        "durgapur": "durgapur",
        "howrah": "howrah",
        "siliguri": "siliguri",
        "asansol": "asansol",
        "bardhaman": "bardhaman",
    }

    CURRENT_SELECTORS = [
        ".company-details h3 a",
        ".company-name-title a",
        ".prod-title a",
        "div.companyname a",
        "h2.companyname a",
        "p.companyname a",
        ".producttitle a",
        ".compny-name a",
        ".lcname a",
        "h3 a[href*='indiamart.com']",
        "h2 a[href*='indiamart.com']",
        ".company-card a",
        ".product-card a",
        "[class*='company-name'] a",
        "[class*='product-title'] a",
    ]

    def _build_urls(self, industry: str, city: str) -> list[str]:
        city_enc = urllib.parse.quote_plus(city)
        industry_enc = urllib.parse.quote_plus(industry)
        city_slug = slugify(city)
        ind_slug = slugify(industry)

        return [
            f"https://dir.indiamart.com/search.mp?ss={industry_enc}&city={city_enc}&prdc=on",
            f"https://www.indiamart.com/search?q={industry_enc}",
            f"https://m.indiamart.com/search?q={industry_enc}",
            f"https://dir.indiamart.com/impcat/{ind_slug}.html?biz={city_slug}",
            f"https://dir.indiamart.com/impcat/{ind_slug}.html",
        ]

    def _parse_any_links(self, html: str, source_url: str) -> list[SeedURL]:
        """Fallback parser that finds any IndiaMart product/company links."""
        soup = BeautifulSoup(html, "lxml")
        seeds: list[SeedURL] = []

        for link in soup.find_all("a", href=True):
            href_attr = link.get("href")
            if not isinstance(href_attr, str):
                continue
            href = href_attr

            if "/proddetail/" in href:
                name = link.get_text(strip=True)
                if name and len(name) > 3:
                    if href.startswith("/"):
                        href = "https://www.indiamart.com" + href
                    seeds.append(
                        SeedURL(
                            url=href,
                            source_name="indiamart_listing",
                            expected_type="company",
                            confidence=0.80,
                        )
                    )

        return seeds[:20]

    async def get_company_urls(
        self, industry: str, city: str, max_pages: int = 3
    ) -> list[SeedURL]:
        seed_urls = self._build_urls(industry, city)
        all_companies: list[SeedURL] = []

        for base_url in seed_urls:
            logger.info(f"indiamart_search_attempt: {base_url}")

            result = await fetch_page(base_url)
            if result.status_code == 404:
                logger.warning(
                    f"indiamart_page_404: {base_url} - skipping to next pattern"
                )
                continue

            if not result.success:
                logger.warning(
                    f"indiamart_page_failed: {base_url} - status {result.status_code}"
                )
                continue

            companies = self._parse_listing_page(result.html, base_url)

            if companies:
                all_companies.extend(companies)
                logger.info(
                    f"indiamart_success: {base_url} got {len(companies)} results"
                )
                break
            else:
                logger.info(f"indiamart_no_results: {base_url} - trying next pattern")

            await asyncio.sleep(1.0)

        seen = set()
        unique: list[SeedURL] = []
        for s in all_companies:
            domain = urlparse(s.url).netloc
            if domain not in seen:
                seen.add(domain)
                unique.append(s)

        logger.info(f"indiamart_search_done: {industry}/{city} found={len(unique)}")
        return unique

    def _parse_listing_page(self, html: str, source_url: str) -> list[SeedURL]:
        soup = BeautifulSoup(html, "lxml")
        seeds: list[SeedURL] = []

        found_links = []
        for selector in self.CURRENT_SELECTORS:
            links = soup.select(selector)
            if links:
                found_links = links
                break

        for link in found_links:
            href_attr = link.get("href")
            if not isinstance(href_attr, str):
                continue
            href = href_attr
            name = link.get_text(strip=True)

            if not href or not name or len(name) < 3:
                continue

            if href.startswith("/"):
                href = "https://www.indiamart.com" + href
            elif not href.startswith("http"):
                continue

            if "indiamart.com" not in href.lower():
                continue

            parent_card = link.find_parent(
                class_=re.compile(
                    r"list|card|company|item|m-cl|r-stpd|product|company", re.I
                )
            )
            website_url: str | None = None
            if parent_card:
                for a in parent_card.find_all("a"):
                    a_href_attr = a.get("href")
                    if isinstance(a_href_attr, str) and a_href_attr.startswith("http"):
                        if "indiamart" not in a_href_attr.lower():
                            website_url = a_href_attr
                            break

            seeds.append(
                SeedURL(
                    url=href,
                    source_name="indiamart_listing",
                    expected_type="company",
                    confidence=0.85,
                )
            )

            if website_url and len(website_url) > 10:
                seeds.append(
                    SeedURL(
                        url=website_url,
                        source_name="indiamart_website",
                        expected_type="company",
                        confidence=0.80,
                    )
                )

        self._extract_listing_snippets(soup, seeds)

        return seeds

    def _extract_listing_snippets(
        self, soup: BeautifulSoup, seeds: list[SeedURL]
    ) -> None:
        for el in soup.select(".phone, .tel, [class*='phone'], [class*='mobile']"):
            phone = el.get_text(strip=True)
            if re.search(r"\d{10}", phone) and seeds:
                seeds[-1].inline_phone = phone
                break

        for el in soup.select(".address, [class*='addr'], .loc"):
            addr = el.get_text(strip=True)
            if len(addr) > 10 and seeds:
                seeds[-1].inline_address = addr
                break


async def test():
    scraper = IndiaMartSearch()
    seeds = await scraper.get_company_urls("oil manufacturers", "kolkata")
    print(f"Found: {len(seeds)} companies")
    for s in seeds[:5]:
        print(f"  {s.url}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test())
