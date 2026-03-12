from __future__ import annotations

import copy
import json
import site
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

PROJECT_ROOT = Path(__file__).parent
PYDEPS = PROJECT_ROOT / "pydeps"
if PYDEPS.exists() and str(PYDEPS) not in sys.path:
    sys.path.insert(0, str(PYDEPS))

user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.append(user_site)

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_args, **_kwargs):
        return False

from fastapi import BackgroundTasks, FastAPI, HTTPException
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

load_dotenv(PROJECT_ROOT / ".env")
LOGGER = setup_logging(PROJECT_ROOT / "output" / "logs")
BASE_SETTINGS = load_settings(PROJECT_ROOT)
PIPELINE = Pipeline()
RESULTS_JSON = PROJECT_ROOT / "output" / "results.json"
RESULTS_CSV = PROJECT_ROOT / "output" / "results.csv"
GOOGLE_CREDS = PROJECT_ROOT / "credentials" / "google_credentials.json"


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


app = FastAPI(title="DataHarvester API", version="0.3.2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

JOBS: list[dict] = []
COMPANIES: list[dict] = []


def _load_results() -> list[dict]:
    if not RESULTS_JSON.exists():
        return []
    try:
        records = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
        for index, record in enumerate(records, start=1):
            record.setdefault("id", str(index))
            record.setdefault("SL No.", str(index))
        return records
    except Exception:
        LOGGER.exception("Failed to load existing results.json")
        return []


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


def _sync_current_records_to_sheets() -> bool:
    if not COMPANIES:
        return False
    append_to_sheet(
        credentials_path=GOOGLE_CREDS,
        sheet_name=BASE_SETTINGS.google_sheet_name,
        worksheet_name=BASE_SETTINGS.google_worksheet_name,
        records=COMPANIES,
    )
    return True


async def _run_scrape_job(job_id: str, payload: StartScrapeRequest) -> None:
    job = next((item for item in JOBS if item["id"] == job_id), None)
    if not job:
        return

    try:
        settings = _configure_settings_for_sources(job["sources"])
        engine = ScraperEngine(settings)
        queries = build_queries([
            QueryInput(
                keyword=payload.keyword.strip(),
                location=payload.location.strip() or None,
                industry=payload.industry.strip() or None,
            )
        ])
        job["progress"] = 15
        LOGGER.info(f"Starting background scrape job {job_id} with {len(queries)} queries")

        scraper_result = await engine.run_async(queries)
        job["progress"] = 70

        final_records = PIPELINE.run(scraper_result.records)
        for index, record in enumerate(final_records, start=1):
            record["id"] = str(index)
            record["SL No."] = str(index)

        COMPANIES.clear()
        COMPANIES.extend(final_records)
        _save_results(final_records)

        job["recordsFound"] = len(final_records)
        job["progress"] = 100
        job["status"] = "Completed"
        LOGGER.info(f"Scrape job {job_id} completed with {len(final_records)} records")
    except Exception as exc:
        job["status"] = "Failed"
        job["progress"] = 100
        LOGGER.exception(f"Scrape job {job_id} failed: {exc}")


@app.on_event("startup")
def startup_event() -> None:
    COMPANIES.clear()
    COMPANIES.extend(_load_results())
    LOGGER.info(f"API startup complete. Loaded {len(COMPANIES)} companies from output/results.json.")


@app.get("/api/jobs")
def get_jobs() -> list[dict]:
    return JOBS


@app.get("/api/companies")
def get_companies() -> list[dict]:
    return COMPANIES


@app.get("/api/company/{company_id}")
def get_company(company_id: str) -> dict:
    company = next((item for item in COMPANIES if item.get("id") == company_id or item.get("SL No.") == company_id), None)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


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


@app.post("/api/push-to-sheets")
def push_to_sheets() -> dict:
    try:
        synced = _sync_current_records_to_sheets()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Google Sheets sync failed: {exc}") from exc

    if not synced:
        raise HTTPException(status_code=400, detail="No records available to sync.")

    return {"success": True, "rows_synced": len(COMPANIES)}
