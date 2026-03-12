from __future__ import annotations

import copy
import json
import os
import re
import site
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional
from uuid import uuid4

user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.append(user_site)

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_args, **_kwargs):
        return False

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.settings import Settings, load_settings
from core.pipeline import Pipeline
from core.scraper_engine import ScraperEngine
from storage.csv_writer import write_csv
from storage.json_writer import write_json
from storage.sheet_writer import append_to_sheet
from utils.logger import setup_logging
from utils.query_builder import QueryInput, build_queries

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")
LOGGER = setup_logging(PROJECT_ROOT / "output" / "logs")
BASE_SETTINGS = load_settings(PROJECT_ROOT)
PIPELINE = Pipeline()
RESULTS_JSON = PROJECT_ROOT / "output" / "results.json"
RESULTS_CSV = PROJECT_ROOT / "output" / "results.csv"
GOOGLE_CREDS = PROJECT_ROOT / "credentials" / "google_credentials.json"
USE_SEED_DATA = os.getenv("DATAHARVESTER_USE_SEED_DATA", "false").lower() in {"1", "true", "yes"}

# ---------------------------------------------------------------------------
# Inline extractor engine (no spaCy needed, works on Python 3.14)
# ---------------------------------------------------------------------------
_EXTRACT_PATTERNS = {
    "emails": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "phones": re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,5}[\s-]?\d{4,6}"),
    "revenue": re.compile(
        r"(?:₹|\$|€|£|Rs\.?|INR|USD)?\s*[\d,.]+\s*(?:Cr|Crore|Million|Billion|Lakh)\b",
        re.IGNORECASE,
    ),
    "erp": re.compile(r"\b(SAP|Oracle|Odoo|Dynamics|NetSuite|Tally|Zoho|Salesforce)\b", re.IGNORECASE),
    "employees": re.compile(
        r"(\d{1,6}\s*(?:\+|employees)|\d{1,6}\s*-\s*\d{1,6}\s*employees)", re.IGNORECASE
    ),
    "roles": re.compile(r"\b(CEO|CFO|CTO|Director|Founder|VP|President|Head|Managing\s*Director)\b", re.IGNORECASE),
}

def _extract_entities(text: str) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    for label, pat in _EXTRACT_PATTERNS.items():
        matches = list({m.strip() for m in pat.findall(text) if m.strip()})
        if matches:
            results[label] = matches
    return results


def _enrich_record(record: dict[str, Any]) -> dict[str, Any]:
    """Append an `_extracted` key with entity-extraction results."""
    combined = " | ".join(str(v) for v in record.values() if v)
    record["_extracted"] = _extract_entities(combined)
    return record


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class StartScrapeRequest(BaseModel):
    keyword: str = Field(min_length=1)
    industry: str = ""
    location: str = ""
    sources: list[Literal["google", "maps", "indiamart", "tradeindia", "justdial", "linkedin", "website"]]


class JobResponse(BaseModel):
    id: str
    query: str
    keyword: str
    industry: str = ""
    location: str = ""
    status: Literal["Running", "Completed", "Failed"]
    recordsFound: int = 0
    startTime: str
    progress: int = 0
    sources: list[str]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="DataHarvester API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS: list[dict] = []
COMPANIES: list[dict] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load_seed_data() -> list[dict]:
    """Optionally load data.json seed records when explicitly enabled."""
    if not USE_SEED_DATA:
        return []

    data_json = PROJECT_ROOT / "data.json"
    if not data_json.exists():
        return []

    try:
        records = json.loads(data_json.read_text(encoding="utf-8"))
        for idx, rec in enumerate(records, start=1):
            if "id" not in rec:
                rec["id"] = str(idx)
            if "SL No." not in rec:
                rec["SL No."] = str(idx)
        return records
    except Exception:
        LOGGER.exception("Failed to load data.json")
        return []


def _load_results_json() -> list[dict]:
    """Load output/results.json (scraped data)."""
    if not RESULTS_JSON.exists():
        return []
    try:
        return json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    except Exception:
        LOGGER.exception("Failed to load existing results.json")
        return []


def _merge_companies(seed: list[dict], scraped: list[dict]) -> list[dict]:
    """Merge seed data.json with any scraped results, deduplicating by company name."""
    seen: set[str] = set()
    merged: list[dict] = []
    for rec in seed + scraped:
        name = (rec.get("Company Name") or rec.get("company_name") or "").strip().lower()
        if name and name in seen:
            continue
        if name:
            seen.add(name)
        merged.append(rec)
    # Re-index
    for idx, rec in enumerate(merged, start=1):
        rec["id"] = str(idx)
        rec["SL No."] = str(idx)
    return merged


def _configure_settings_for_sources(sources: list[str]) -> Settings:
    settings = copy.deepcopy(BASE_SETTINGS)
    enabled = set(sources)
    settings.platforms.google = "google" in enabled
    settings.platforms.maps = "maps" in enabled
    settings.platforms.linkedin = "linkedin" in enabled
    settings.platforms.website = "website" in enabled
    settings.platforms.indiamart = "indiamart" in enabled
    settings.platforms.tradeindia = "tradeindia" in enabled
    settings.platforms.justdial = "justdial" in enabled
    settings.platforms.clutch = False
    settings.platforms.goodfirms = False
    return settings


def _save_results(records: list[dict]) -> None:
    write_json(RESULTS_JSON, records)
    write_csv(RESULTS_CSV, records)
    try:
        append_to_sheet(
            credentials_path=GOOGLE_CREDS,
            sheet_name=BASE_SETTINGS.google_sheet_name,
            worksheet_name=BASE_SETTINGS.google_worksheet_name,
            records=records,
        )
    except Exception:
        LOGGER.warning("Sheet sync skipped (credentials may not be configured).")


# ---------------------------------------------------------------------------
# Background scrape job
# ---------------------------------------------------------------------------
async def _run_scrape_job(job_id: str, payload: StartScrapeRequest) -> None:
    job = next((item for item in JOBS if item["id"] == job_id), None)
    if not job:
        return

    try:
        settings = _configure_settings_for_sources(job["sources"])
        engine = ScraperEngine(settings)
        raw_inputs = [
            QueryInput(
                keyword=payload.keyword.strip(),
                location=payload.location.strip() or None,
                industry=payload.industry.strip() or None,
            )
        ]
        queries = build_queries(raw_inputs)
        job["progress"] = 15
        LOGGER.info(f"Starting background scrape job {job_id} with {len(queries)} queries")

        scraper_result = await engine.run_async(queries)
        job["progress"] = 70

        final_records = PIPELINE.run(scraper_result.records)
        for index, record in enumerate(final_records, start=1):
            record["id"] = str(index)

        # Merge with existing in-memory results (and optional seed)
        merged = _merge_companies(COMPANIES, final_records)
        COMPANIES.clear()
        COMPANIES.extend(merged)
        _save_results(merged)

        job["recordsFound"] = len(final_records)
        job["progress"] = 100
        job["status"] = "Completed"
        LOGGER.info(f"Scrape job {job_id} completed with {len(final_records)} records")
    except Exception as exc:
        job["status"] = "Failed"
        job["progress"] = 100
        LOGGER.exception(f"Scrape job {job_id} failed: {exc}")


# ---------------------------------------------------------------------------
# Startup — loads prior scrape results; seed data is opt-in via env var
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup_event() -> None:
    COMPANIES.clear()
    seed = _load_seed_data()
    scraped = _load_results_json()
    merged = _merge_companies(seed, scraped)
    COMPANIES.extend(merged)
    LOGGER.info(
        f"API startup complete. Loaded {len(COMPANIES)} companies "
        f"({len(seed)} seed records, {len(scraped)} from prior scrape results)."
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/api/jobs")
def get_jobs() -> list[dict]:
    return JOBS


@app.get("/api/companies")
def get_companies(
    location: Optional[str] = Query(None, description="Filter by location (case-insensitive substring match)")
) -> list[dict]:
    if location:
        loc_lower = location.lower()
        return [c for c in COMPANIES if loc_lower in (c.get("Address") or "").lower()]
    return COMPANIES


@app.get("/api/company/{company_id}")
def get_company(company_id: str) -> dict:
    company = next((item for item in COMPANIES if item.get("id") == company_id or item.get("SL No.") == company_id), None)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@app.get("/api/extract")
def extract_from_data() -> dict:
    """
    Run the pattern-based extraction engine on currently available records
    and return the enriched dataset with extracted entities (emails, phones,
    revenue, ERP, leadership roles, employee count).
    """
    enriched = [_enrich_record(rec) for rec in COMPANIES]
    return {"count": len(enriched), "companies": enriched}


@app.post("/api/start-scrape")
def start_scrape(payload: StartScrapeRequest, background_tasks: BackgroundTasks) -> dict:
    job = JobResponse(
        id=f"JOB-{uuid4().hex[:8].upper()}",
        query=" ".join(part for part in [payload.keyword, payload.industry, payload.location] if part).strip(),
        keyword=payload.keyword.strip(),
        industry=payload.industry.strip(),
        location=payload.location.strip(),
        status="Running",
        recordsFound=0,
        startTime=datetime.now(timezone.utc).isoformat(),
        progress=5,
        sources=payload.sources,
    ).model_dump()
    JOBS.insert(0, job)
    background_tasks.add_task(_run_scrape_job, job["id"], payload)
    return job
