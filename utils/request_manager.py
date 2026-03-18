"""
Smart HTTP + Browser request manager.

- HTTP requests: aiohttp with rotating proxy, random UA, rate limiting
- Browser requests: Playwright stealth mode for JS-heavy / bot-protected sites
- Per-request proxy rotation: each browser context gets its own proxy IP
"""

from __future__ import annotations

import asyncio
import random
import ssl
from typing import Any, Dict, Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.proxy_manager import get_proxy_for_request
from utils.rate_limiter import RateLimiter
from utils.browser_manager import BrowserManager


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# Sites that need full JS rendering / have strong anti-bot protection
BROWSER_REQUIRED_DOMAINS = {
    "bing.com",
    "duckduckgo.com",
    "google.com",
    "search.yahoo.com",
    "linkedin.com",
    "justdial.com",
    "clutch.co",
    "goodfirms.co",
    "indiamart.com",
    "tradeindia.com",
    "searx",
    "search.",
}


class RequestManager:
    def __init__(
        self,
        proxy_config: Dict[str, Any] | None = None,
        timeout: int = 30,
        delay_seconds: float = 1.2,
        concurrency: int = 4,
    ) -> None:
        self.proxy_config = proxy_config or {}
        self.timeout = timeout
        self.delay_seconds = delay_seconds

        self._session: Optional[aiohttp.ClientSession] = None
        self._limiter = RateLimiter(
            rate_per_sec=max(0.5, 1 / max(delay_seconds, 0.1)),
            burst=max(1, concurrency),
        )
        self._semaphore = asyncio.Semaphore(concurrency)
        self.browser = BrowserManager()

    # ------------------------------------------------------------------
    # Smart fetch: browser for JS-heavy domains, HTTP otherwise
    # ------------------------------------------------------------------

    async def fetch(self, url: str, *, headers: Dict[str, str] | None = None) -> str:
        """
        Automatically choose between stealth browser and HTTP.
        Browser is used for known JS-heavy / bot-protected domains.
        Each browser fetch gets its own proxy from the rotating pool.
        Falls back to HTTP if browser fails or Playwright is unavailable.
        """
        domain = _extract_domain(url)
        use_browser = self.browser.available and any(
            blocked in domain for blocked in BROWSER_REQUIRED_DOMAINS
        )

        if use_browser:
            try:
                # Grab a fresh proxy from the pool for this browser context
                proxy = get_proxy_for_request(self.proxy_config)
                return await self.browser.fetch(url, proxy_url=proxy)
            except Exception:
                pass  # fall through to HTTP

        return await self.get_text(url, headers=headers)

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "RequestManager":
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=20)
        self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session:
            await self._session.close()
            self._session = None
        # Close the persistent browser if it was opened
        if self.browser and self.browser.available:
            try:
                await self.browser.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # HTTP fetch with retry + rate limiting + rotating proxy
    # ------------------------------------------------------------------

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=15), stop=stop_after_attempt(3)
    )
    async def get_text(self, url: str, *, headers: Dict[str, str] | None = None) -> str:
        if not self._session:
            raise RuntimeError(
                "RequestManager used outside context manager.\n"
                "Use: async with RequestManager(...) as rm:"
            )

        # Get next proxy from rotating pool
        proxy = get_proxy_for_request(self.proxy_config)

        base_headers: Dict[str, str] = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
        }
        if headers:
            base_headers.update(headers)

        async with self._semaphore:
            async with self._limiter.limit():
                if self.delay_seconds > 0:
                    await asyncio.sleep(
                        random.uniform(
                            self.delay_seconds * 0.6,
                            self.delay_seconds * 1.5,
                        )
                    )

                async with self._session.get(
                    url,
                    headers=base_headers,
                    proxy=proxy,
                    allow_redirects=True,
                ) as resp:
                    resp.raise_for_status()
                    return await resp.text()


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse

        return urlparse(url).netloc.lower()
    except Exception:
        return ""
