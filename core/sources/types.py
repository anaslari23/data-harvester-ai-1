from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


@dataclass
class FetchResult:
    success: bool = False
    html: str = ""
    status_code: int = 0
    error: str = ""


@dataclass
class SeedURL:
    url: str
    source_name: str = ""
    expected_type: str = "company"
    confidence: float = 0.5
    inline_phone: Optional[str] = None
    inline_email: Optional[str] = None
    inline_address: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def domain(self) -> str:
        try:
            return urlparse(self.url).netloc
        except Exception:
            return ""
