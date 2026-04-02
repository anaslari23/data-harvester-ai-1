from __future__ import annotations

import asyncio
import re
import urllib.parse
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from loguru import logger

from core.sources.http_utils import fetch_page
from core.sources.indiamart_search import IndiaMartSearch
from core.sources.justdial_search import JustDialSearch
from core.sources.types import SeedURL, slugify


def _extract_real_url(href: str) -> str:
    """
    DDG wraps real URLs in redirect:
      //duckduckgo.com/l/?uddg=https%3A%2F%2Factualsite.com
    Extract and decode the actual target URL.
    """
    if not href:
        return ""

    # Handle DDG redirect URLs
    if "duckduckgo.com/l/" in href:
        parsed = urllib.parse.urlparse(href)
        params = urllib.parse.parse_qs(parsed.query)
        uddg = params.get("uddg", [""])[0]
        if uddg:
            return urllib.parse.unquote(uddg)

    # Handle protocol-relative URLs
    if href.startswith("//"):
        return "https:" + href

    return href


async def duckduckgo_search(query: str, max_results: int = 20) -> list[SeedURL]:
    seeds: list[SeedURL] = []
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

    result = await fetch_page(url)
    if not result.success:
        return seeds

    _skip_domains = [
        "duckduckgo.com", "google.com", "bing.com",
        "yahoo.com", "baidu.com", "yandex.com",
    ]

    soup = BeautifulSoup(result.html, "lxml")
    for item in soup.select("div.result__body")[:max_results]:
        link_el = item.select_one("a.result__a, a.result__url")
        if not link_el:
            continue
        href = link_el.get("href", "")

        real_url = _extract_real_url(href)
        if not real_url or not real_url.startswith("http"):
            continue
        if any(d in real_url for d in _skip_domains):
            continue

        seeds.append(
            SeedURL(
                url=real_url,
                source_name="duckduckgo",
                expected_type="company",
                confidence=0.60,
            )
        )

    return seeds


async def discover_seeds(
    industry: str,
    cities: list[str],
    sources: list[str] | None = None,
    max_results: int = 100,
) -> tuple[list[SeedURL], str]:
    all_seeds: list[SeedURL] = []
    mode = "directory"

    indiamart_search = IndiaMartSearch()
    justdial_search = JustDialSearch()

    for city in cities:
        logger.info(f"discovery_indiamart: {industry}/{city}")
        im_seeds = await indiamart_search.get_company_urls(industry, city, max_pages=3)
        all_seeds.extend(im_seeds)
        logger.info(f"discovery_indiamart_done: {city} found={len(im_seeds)}")
        await asyncio.sleep(2.0)

        if len(all_seeds) < 10:
            logger.info(f"discovery_justdial: {industry}/{city}")
            jd_seeds = await justdial_search.get_company_urls(industry, city)
            all_seeds.extend(jd_seeds)
            logger.info(f"discovery_justdial_done: {city} found={len(jd_seeds)}")
            await asyncio.sleep(2.0)

    if len(all_seeds) < max_results:
        logger.info("discovery_web_search_supplement")
        queries = [f"{industry} {city}" for city in cities]
        for q in queries[:5]:
            web = await duckduckgo_search(q, 20)
            all_seeds.extend(web)
            await asyncio.sleep(2.0)

        if any(all_seeds):
            mode = "hybrid"

    seen_external: set[str] = set()
    seen_marketplace: set[str] = set()
    unique: list[SeedURL] = []
    marketplace_domains = {
        "www.justdial.com",
        "justdial.com",
        "www.indiamart.com",
        "indiamart.com",
        "www.tradeindia.com",
        "tradeindia.com",
    }

    for s in all_seeds:
        try:
            url = s.url
            domain = urlparse(url).netloc
            domain_clean = domain.replace("www.", "").replace("m.", "")

            if domain_clean in marketplace_domains:
                # For marketplace profile pages, dedupe by URL path (different companies)
                path = urlparse(url).path
                if path not in seen_marketplace:
                    seen_marketplace.add(path)
                    unique.append(s)
            else:
                # For external websites, dedupe by domain
                if domain_clean and domain_clean not in seen_external:
                    seen_external.add(domain_clean)
                    unique.append(s)
        except Exception:
            continue

    logger.info(
        "discovery_complete",
        total=len(unique),
        mode=mode,
        indiamart=sum(1 for s in unique if "indiamart" in s.source_name),
        justdial=sum(1 for s in unique if "justdial" in s.source_name),
        web=sum(1 for s in unique if s.source_name == "duckduckgo"),
    )

    return unique[:max_results], mode


def seeds_to_records(seeds: list[SeedURL]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for seed in seeds:
        record: dict[str, Any] = {
            "company_name": "",
            "website": "",
            "phone": seed.inline_phone or "",
            "email": seed.inline_email or "",
            "address": seed.inline_address or "",
            "city": "",
            "state": "",
            "country": "India",
            "industry_type": "",
            "employee_count": "",
            "turnover": "",
            "erp_software": "",
            "contact_name": "",
            "owner_role": "",
            "description": "",
            "additional_info": f"Source: {seed.source_name} | Confidence: {seed.confidence}",
            "source": seed.source_name,
            "source_url": seed.url,
        }

        if (
            seed.source_name == "indiamart_website"
            or seed.source_name == "justdial_website"
        ):
            record["website"] = seed.url
        elif "indiamart" in seed.source_name:
            record["additional_info"] = (
                f"{record['additional_info']} | Profile: {seed.url}"
            )
        elif "justdial" in seed.source_name:
            record["additional_info"] = (
                f"{record['additional_info']} | Profile: {seed.url}"
            )

        records.append(record)

    return records
