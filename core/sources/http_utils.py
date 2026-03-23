from __future__ import annotations

import asyncio
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from core.sources.types import FetchResult


async def fetch_page(url: str, timeout: float = 20.0) -> FetchResult:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = await client.get(url, headers=headers)
            return FetchResult(
                success=response.status_code == 200,
                html=response.text,
                status_code=response.status_code,
            )
    except httpx.TimeoutException:
        return FetchResult(success=False, error="Timeout")
    except httpx.RequestError as exc:
        return FetchResult(success=False, error=str(exc))
    except Exception as exc:
        return FetchResult(success=False, error=str(exc))


def extract_phones_from_text(text: str) -> list[str]:
    phone_patterns = [
        r"(?:\+91[\s\-]?)?[6-9]\d{9}",
        r"\b\d{10}\b",
        r"\b\d{3}[\s\-]\d{3}[\s\-]\d{4}\b",
        r"\(\d{3}\)\s?\d{3}[\s\-]\d{4}",
    ]
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            cleaned = re.sub(r"[^\d+]", "", match)
            if len(cleaned) >= 10:
                phones.append(match.strip())
    return list(set(phones))


def extract_emails_from_text(text: str) -> list[str]:
    email_pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    return re.findall(email_pattern, text)
