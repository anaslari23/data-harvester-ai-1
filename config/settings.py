from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class PlatformSettings:
    discovery: bool = True
    google: bool = True
    maps: bool = True
    linkedin: bool = True
    website: bool = True
    indiamart: bool = True
    tradeindia: bool = True
    justdial: bool = True
    clutch: bool = True
    goodfirms: bool = True
    google_places: bool = False
    searx: bool = True


@dataclass
class ProxySettings:
    enabled: bool = False
    mode: str = "pool"  # pool | webshare | brightdata | smartproxy | custom
    http: str | None = None
    https: str | None = None
    url: str | None = None  # for mode=custom
    endpoint: str | None = None  # for mode=webshare/brightdata/smartproxy
    username: str | None = None
    password: str | None = None
    rotation_strategy: str = "round_robin"  # round_robin | random
    list: list = field(default_factory=list)  # for mode=pool


@dataclass
class Settings:
    project_root: Path
    platforms: PlatformSettings = field(default_factory=PlatformSettings)
    proxies: ProxySettings = field(default_factory=ProxySettings)
    google_sheet_name: str = "DataHarvester Results"
    google_worksheet_name: str = "Companies"


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings(project_root: Path) -> Settings:
    raw_platforms_cfg = _load_yaml(project_root / "config" / "platforms.yaml")
    platforms_cfg = raw_platforms_cfg.get("platforms", raw_platforms_cfg)
    proxies_cfg = _load_yaml(project_root / "config" / "proxies.yaml").get(
        "proxies", {}
    )

    platforms = PlatformSettings(
        discovery=bool(platforms_cfg.get("discovery", True)),
        google=bool(platforms_cfg.get("google", True)),
        maps=bool(platforms_cfg.get("maps", True)),
        linkedin=bool(platforms_cfg.get("linkedin", True)),
        website=bool(platforms_cfg.get("website", True)),
        indiamart=bool(platforms_cfg.get("indiamart", True)),
        tradeindia=bool(platforms_cfg.get("tradeindia", True)),
        justdial=bool(platforms_cfg.get("justdial", True)),
        clutch=bool(platforms_cfg.get("clutch", True)),
        goodfirms=bool(platforms_cfg.get("goodfirms", True)),
        google_places=bool(platforms_cfg.get("google_places", False)),
        searx=bool(platforms_cfg.get("searx", True)),
    )

    proxies = ProxySettings(
        enabled=bool(proxies_cfg.get("enabled", False)),
        mode=proxies_cfg.get("mode", "pool"),
        http=proxies_cfg.get("http"),
        https=proxies_cfg.get("https"),
        url=proxies_cfg.get("url"),
        endpoint=proxies_cfg.get("endpoint"),
        username=proxies_cfg.get("username"),
        password=proxies_cfg.get("password"),
        rotation_strategy=proxies_cfg.get("rotation_strategy", "round_robin"),
        list=proxies_cfg.get("list", []),
    )

    return Settings(project_root=project_root, platforms=platforms, proxies=proxies)
