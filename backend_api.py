from __future__ import annotations

import copy
import csv
import io
import json
import os
import site
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
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

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from config.settings import Settings, load_settings
from core.pipeline import Pipeline
from core.scraper_engine import ScraperEngine
from storage.csv_writer import write_csv
from storage.json_writer import write_json
from storage.sheet_writer import append_to_sheet
from storage.supabase_writer import get_all_jobs, upsert_job, get_all_companies, upsert_companies, clear_all_jobs
from utils.logger import setup_logging
from utils.query_builder import QueryInput, build_queries

load_dotenv(PROJECT_ROOT / ".env")
LOGGER = setup_logging(PROJECT_ROOT / "output" / "logs")
BASE_SETTINGS = load_settings(PROJECT_ROOT)
PIPELINE = Pipeline()

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
RESULTS_JSON = OUTPUT_DIR / "results.json"
RESULTS_CSV = OUTPUT_DIR / "results.csv"
JOBS_JSON = OUTPUT_DIR / "jobs.json"          # <-- persisted job store


def _resolve_google_creds_path() -> Path:
    configured = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
    if configured:
        candidate = Path(configured)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        return candidate

    fallback_candidates = [
        PROJECT_ROOT / "credentials" / "google_credentials.json",
        PROJECT_ROOT / "credentials" / "service_account.json",
        PROJECT_ROOT / "service_account.json",
    ]
    for candidate in fallback_candidates:
        if candidate.exists():
            return candidate

    return fallback_candidates[0]


def _google_sheet_name() -> str:
    return os.getenv("GOOGLE_SHEET_NAME", BASE_SETTINGS.google_sheet_name).strip() or BASE_SETTINGS.google_sheet_name


def _google_worksheet_name() -> str:
    return os.getenv("GOOGLE_WORKSHEET_NAME", BASE_SETTINGS.google_worksheet_name).strip() or BASE_SETTINGS.google_worksheet_name


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class StartScrapeRequest(BaseModel):
    keyword: str = Field(min_length=1)
    industry: str = ""
    location: str = ""
    sources: list[Literal[
        "google", "maps", "indiamart", "tradeindia", "justdial",
        "linkedin", "website", "clutch", "goodfirms", "google_places",
        "searx", "direct_website", "discovery",
    ]]


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
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — reload persisted state from disk/Supabase
    JOBS.clear()
    JOBS.extend(_load_jobs())
    COMPANIES.clear()
    COMPANIES.extend(_load_results())
    LOGGER.info(
        "API startup: loaded %d jobs and %d companies from disk",
        len(JOBS), len(COMPANIES),
    )
    yield
    # Shutdown (if needed)
    pass

app = FastAPI(
    title="Data Harvester API",
    description="API for data scraping and extraction",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# In-memory state (also persisted to disk)
JOBS: list[dict] = []
COMPANIES: list[dict] = []


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _load_results() -> list[dict]:
    db_records = get_all_companies()
    if db_records:
        return db_records

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


def _load_jobs() -> list[dict]:
    """Restore jobs from disk or Supabase so they survive API restarts."""
    db_jobs = get_all_jobs()
    if db_jobs:
        return db_jobs

    if not JOBS_JSON.exists():
        return []
    try:
        return json.loads(JOBS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_jobs() -> None:
    """Persist current JOBS list to disk and Supabase."""
    try:
        JOBS_JSON.write_text(json.dumps(JOBS, indent=2), encoding="utf-8")
    except Exception:
        LOGGER.warning("Could not persist jobs to disk")
    
    if JOBS:
        upsert_job(JOBS)


def _save_results(records: list[dict]) -> None:
    write_json(RESULTS_JSON, records)
    write_csv(RESULTS_CSV, records)
    if records:
        upsert_companies(records)


def _sync_to_sheets() -> int:
    """Push current COMPANIES to Google Sheets and return synced row count."""
    if not COMPANIES:
        raise ValueError("No records available to sync.")

    credentials_path = _resolve_google_creds_path()
    if not credentials_path.exists():
        raise FileNotFoundError(
            "Google service account file was not found. "
            f"Checked: {credentials_path}. Update GOOGLE_SERVICE_ACCOUNT_FILE or place the JSON there."
        )

    append_to_sheet(
        credentials_path=credentials_path,
        sheet_name=_google_sheet_name(),
        worksheet_name=_google_worksheet_name(),
        records=COMPANIES,
    )
    return len(COMPANIES)


# ---------------------------------------------------------------------------
# Settings helper
# ---------------------------------------------------------------------------

def _configure_settings_for_sources(sources: list[str]) -> Settings:
    settings = copy.deepcopy(BASE_SETTINGS)
    enabled = set(sources)
    settings.platforms.discovery = "discovery" in enabled
    settings.platforms.google = "google" in enabled
    settings.platforms.maps = "maps" in enabled
    settings.platforms.linkedin = "linkedin" in enabled
    settings.platforms.website = "website" in enabled
    settings.platforms.indiamart = "indiamart" in enabled
    settings.platforms.tradeindia = "tradeindia" in enabled
    settings.platforms.justdial = "justdial" in enabled
    settings.platforms.clutch = "clutch" in enabled
    settings.platforms.goodfirms = "goodfirms" in enabled
    settings.platforms.google_places = "google_places" in enabled
    settings.platforms.searx = "searx" in enabled
    settings.platforms.direct_website = "direct_website" in enabled
    return settings


# ---------------------------------------------------------------------------
# Background job runner
# ---------------------------------------------------------------------------

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
        _save_jobs()
        LOGGER.info("Starting background scrape job %s with %d queries", job_id, len(queries))

        def update_progress(pct: int):
            job["progress"] = pct
            job["status"] = "Running"
            _save_jobs()

        scraper_result = await engine.run_async(queries, progress_callback=update_progress)
        job["progress"] = 85
        _save_jobs()

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
        _save_jobs()
        LOGGER.info("Scrape job %s completed with %d records", job_id, len(final_records))

    except Exception as exc:
        job["status"] = "Failed"
        job["progress"] = 100
        _save_jobs()
        LOGGER.exception("Scrape job %s failed: %s", job_id, exc)


async def _run_bulk_scrape_job(job_id: str, query_inputs: list[QueryInput], sources: list[str]) -> None:
    """Background runner for bulk JSON/CSV upload scrapes."""
    job = next((item for item in JOBS if item["id"] == job_id), None)
    if not job:
        return

    try:
        settings = _configure_settings_for_sources(sources)
        engine = ScraperEngine(settings)
        queries = build_queries(query_inputs)

        job["progress"] = 15
        _save_jobs()
        LOGGER.info("Starting bulk scrape job %s with %d input rows → %d queries", job_id, len(query_inputs), len(queries))

        def update_progress(pct: int):
            job["progress"] = pct
            job["status"] = "Running"
            _save_jobs()

        scraper_result = await engine.run_async(queries, progress_callback=update_progress)
        job["progress"] = 85
        _save_jobs()

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
        _save_jobs()
        LOGGER.info("Bulk scrape job %s completed with %d records", job_id, len(final_records))

    except Exception as exc:
        job["status"] = "Failed"
        job["progress"] = 100
        _save_jobs()
        LOGGER.exception("Bulk scrape job %s failed: %s", job_id, exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/parse-query")
def parse_natural_language_query(body: dict) -> dict:
    """
    Parse a natural language query string into structured keyword/location/industry fields.
    e.g. "Find wholesale furniture manufacturers in Mumbai" →
         {"keyword": "wholesale furniture manufacturers", "location": "Mumbai", "industry": ""}
    """
    import re
    text = str(body.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    keyword = text

    # Remove leading action verbs
    keyword = re.sub(
        r"^(?:find|get|search\s+for|look\s+for|discover|show\s+me|"
        r"list|give\s+me|fetch|scrape|i\s+want|i\s+need)\s+",
        "", keyword, flags=re.IGNORECASE,
    ).strip()

    # Extract location via prepositions ("in X", "near X", "from X", "at X", "around X")
    location = ""
    loc_pattern = (
        r"\b(?:in|near|from|at|around|across)\s+"
        r"([A-Za-z][a-zA-Z\s]+?)"
        r"(?=\s+(?:who|that|which|providing|with|for|and|,|\.|$)|[,.]|$)"
    )
    loc_match = re.search(loc_pattern, keyword, re.IGNORECASE)
    if loc_match:
        location = loc_match.group(1).strip().rstrip(".,")
        keyword = (keyword[: loc_match.start()] + " " + keyword[loc_match.end() :]).strip()

    keyword = re.sub(r"\s+", " ", keyword).strip()
    return {"keyword": keyword, "location": location, "industry": ""}


@app.get("/api/health")
def health_check() -> dict:
    """Simple liveness check used by the frontend Settings page."""
    return {"status": "ok", "jobs": len(JOBS), "companies": len(COMPANIES)}


@app.get("/api/jobs")
def get_jobs() -> list[dict]:
    return JOBS


@app.get("/api/companies")
def get_companies() -> list[dict]:
    return COMPANIES


@app.get("/api/company/{company_id}")
def get_company(company_id: str) -> dict:
    company = next(
        (item for item in COMPANIES
         if item.get("id") == company_id or item.get("SL No.") == company_id),
        None,
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@app.post("/api/start-scrape")
def start_scrape(payload: StartScrapeRequest, background_tasks: BackgroundTasks) -> dict:
    job = JobResponse(
        id=f"JOB-{uuid4().hex[:8].upper()}",
        query=" ".join(p for p in [payload.keyword, payload.industry, payload.location] if p).strip(),
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
    _save_jobs()
    background_tasks.add_task(_run_scrape_job, job["id"], payload)
    return job


@app.post("/api/upload-params")
async def upload_params(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sources: str = "google,maps,indiamart,tradeindia,justdial,linkedin",
) -> dict:
    """
    Upload a JSON or CSV file containing scrape parameters.

    **JSON format** (list of objects):
    ```json
    [
      {"keyword": "ERP software", "location": "Mumbai", "industry": "Manufacturing"},
      {"keyword": "SAP partners", "location": "Delhi"}
    ]
    ```

    **CSV format** (with header row):
    ```
    keyword,location,industry
    ERP software,Mumbai,Manufacturing
    SAP partners,Delhi,
    ```

    The `sources` query param is a comma-separated list:
    google,maps,indiamart,tradeindia,justdial,linkedin,website
    """
    content = await file.read()

    # Parse sources
    source_list: list[str] = [s.strip() for s in sources.split(",") if s.strip()]
    valid_sources = {
        "google", "maps", "indiamart", "tradeindia", "justdial", "linkedin",
        "website", "clutch", "goodfirms", "google_places", "searx", "direct_website", "discovery",
    }
    source_list = [s for s in source_list if s in valid_sources]
    if not source_list:
        source_list = ["google", "maps", "indiamart", "tradeindia", "justdial", "linkedin", "searx"]

    # Parse the uploaded file
    query_inputs: list[QueryInput] = []
    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".json"):
            rows: list[dict[str, Any]] = json.loads(content.decode("utf-8"))
            if not isinstance(rows, list):
                raise HTTPException(status_code=400, detail="JSON must be a list of objects")
            for row in rows:
                keyword_candidates = ["keyword", "Company Name", "company_name", "Company", "Website", "website"]
                keyword = next((str(row.get(k, "")).strip() for k in keyword_candidates if row.get(k)), "")
                if not keyword:
                    continue
                location = str(row.get("location", "") or row.get("Address", "") or "").strip()
                industry = str(row.get("industry", "") or row.get("Industry_Type", "") or row.get("industry_type", "") or "").strip()
                query_inputs.append(QueryInput(
                    keyword=keyword,
                    location=location or None,
                    industry=industry or None,
                ))

        elif filename.endswith(".csv"):
            text = content.decode("utf-8-sig")  # handle BOM
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                keyword_candidates = ["keyword", "Company Name", "company_name", "Company", "Website", "website"]
                keyword = next((str(row.get(k, "")).strip() for k in keyword_candidates if row.get(k)), "")
                if not keyword:
                    continue
                location = str(row.get("location", "") or row.get("Address", "") or "").strip()
                industry = str(row.get("industry", "") or row.get("Industry_Type", "") or row.get("industry_type", "") or "").strip()
                query_inputs.append(QueryInput(
                    keyword=keyword,
                    location=location or None,
                    industry=industry or None,
                ))
        else:
            raise HTTPException(
                status_code=400,
                detail="Only .json and .csv files are supported",
            )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {exc}") from exc

    if not query_inputs:
        raise HTTPException(status_code=400, detail="No valid rows found in the uploaded file")

    # Create a bulk job
    first_keyword = query_inputs[0].keyword
    job_label = f"{first_keyword} (+{len(query_inputs) - 1} more)" if len(query_inputs) > 1 else first_keyword

    job: dict[str, Any] = {
        "id": f"BULK-{uuid4().hex[:8].upper()}",
        "query": job_label,
        "keyword": first_keyword,
        "industry": query_inputs[0].industry or "",
        "location": query_inputs[0].location or "",
        "status": "Running",
        "recordsFound": 0,
        "startTime": datetime.now(timezone.utc).isoformat(),
        "progress": 5,
        "sources": source_list,
        "rowCount": len(query_inputs),
        "filename": file.filename,
    }
    JOBS.insert(0, job)
    _save_jobs()

    background_tasks.add_task(_run_bulk_scrape_job, job["id"], query_inputs, source_list)

    return {
        "job": job,
        "parsed_rows": len(query_inputs),
        "sources": source_list,
        "message": f"Bulk scrape started for {len(query_inputs)} parameter rows",
    }


@app.post("/api/push-to-sheets")
def push_to_sheets() -> dict:
    try:
        rows_synced = _sync_to_sheets()
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.warning("Google Sheets sync blocked: {}", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        LOGGER.exception("Google Sheets sync failed")
        raise HTTPException(status_code=500, detail=f"Google Sheets sync failed: {exc}") from exc

    return {"success": True, "rows_synced": rows_synced}


@app.get("/api/download/csv")
def download_csv() -> dict:
    """Returns path information for downloading the results CSV."""
    if not RESULTS_CSV.exists():
        raise HTTPException(status_code=404, detail="No results CSV found. Run a scrape first.")
    return {
        "path": str(RESULTS_CSV),
        "size_bytes": RESULTS_CSV.stat().st_size,
        "records": len(COMPANIES),
    }


@app.delete("/api/jobs")
def clear_jobs() -> dict:
    """Clear all job history."""
    JOBS.clear()
    _save_jobs()
    clear_all_jobs()
    return {"cleared": True}
