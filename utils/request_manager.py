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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
]


class RequestManager:

    def __init__(
        self,
        proxy_config: Dict[str, Any] | None = None,
        timeout: int = 20,
        delay_seconds: float = 1.0,
        concurrency: int = 5,
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

    # ---------------------------------------------------------
    # Browser first → fallback to HTTP
    # ---------------------------------------------------------

    async def fetch(self, url: str) -> str:

        try:
            # Try Playwright browser rendering
            return await self.browser.fetch(url)

        except Exception:

            # Browser failed → fallback to HTTP
            if not self._session:

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                connector = aiohttp.TCPConnector(ssl=ssl_context)

                async with aiohttp.ClientSession(connector=connector) as session:

                    async with session.get(url) as resp:
                        return await resp.text()

            return await self.get_text(url)

    # ---------------------------------------------------------
    # Session lifecycle
    # ---------------------------------------------------------

    async def __aenter__(self) -> "RequestManager":

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)

        self._session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector
        )

        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:

        if self._session:
            await self._session.close()
            self._session = None

    # ---------------------------------------------------------
    # HTTP Fetch with retry + rate limit
    # ---------------------------------------------------------

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def get_text(self, url: str, *, headers: Dict[str, str] | None = None) -> str:

        if not self._session:
            raise RuntimeError("RequestManager session not initialized")

        proxy = get_proxy_for_request(self.proxy_config)

        base_headers: Dict[str, str] = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

        if headers:
            base_headers.update(headers)

        async with self._semaphore:

            async with self._limiter.limit():

                if self.delay_seconds > 0:

                    await asyncio.sleep(
                        random.uniform(
                            self.delay_seconds * 0.5,
                            self.delay_seconds * 1.5
                        )
                    )

                async with self._session.get(
                    url,
                    headers=base_headers,
                    proxy=proxy
                ) as resp:

                    resp.raise_for_status()

                    return await resp.text()