from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from loguru import logger

from config.settings import Settings
from core.job_manager import JobManager
from core.pipeline import Pipeline
from core.scheduler import Scheduler
from core.scraper_engine import ScraperEngine
from core.sources.search_discovery import discover_seeds, seeds_to_records
from storage.csv_writer import write_csv
from storage.json_writer import write_json
from storage.sheet_writer import append_to_sheet
from utils.query_builder import QueryInput, build_queries


class Orchestrator:
    def __init__(self, project_root: Path, settings: Settings, logger_instance) -> None:
        self.project_root = project_root
        self.settings = settings
        self.logger = logger_instance
        self.engine = ScraperEngine(settings)
        self.pipeline = Pipeline()
        self.job_manager = JobManager()
        self.scheduler = Scheduler()

    def _load_input_queries(self) -> List[QueryInput]:
        input_path = self.project_root / "input" / "queries.csv"
        if not input_path.exists():
            logger.warning(f"No input file found at {input_path}, nothing to do.")
            return []
        df = pd.read_csv(input_path)
        queries: List[QueryInput] = []
        for _, row in df.iterrows():

            def _str(v: Any) -> str:
                if pd.isna(v) or v is None:
                    return ""
                s = str(v).strip()
                return "" if s.lower() == "nan" else s

            keyword = _str(row.get("keyword", ""))
            loc = _str(row.get("location", ""))
            ind = _str(row.get("industry", ""))
            queries.append(
                QueryInput(
                    keyword=keyword,
                    location=loc or None,
                    industry=ind or None,
                )
            )
        return queries

    def _is_indian_sme_query(self, query: QueryInput) -> bool:
        indian_cities = [
            "kolkata",
            "mumbai",
            "delhi",
            "bangalore",
            "bengaluru",
            "hyderabad",
            "chennai",
            "pune",
            "ahmedabad",
            "surat",
            "jaipur",
            "lucknow",
            "kanpur",
            "nagpur",
            "jamshedpur",
            "durgapur",
            "howrah",
            "siliguri",
            "asansol",
            "bardhaman",
            "india",
        ]
        indian_industries = [
            "manufacturer",
            "oil",
            "lubricant",
            "chemical",
            "steel",
            "textile",
            "garment",
            "plastic",
            "food",
            "pharma",
            "engineering",
            "construction",
            "electronics",
            "furniture",
        ]

        loc = (query.location or "").lower()
        ind = (query.keyword or query.industry or "").lower()

        has_indian_city = any(city in loc for city in indian_cities)
        has_indian_industry = any(ind_cat in ind for ind_cat in indian_industries)

        return has_indian_city and has_indian_industry

    async def _run_directory_discovery(
        self, raw_inputs: List[QueryInput]
    ) -> List[Dict[str, Any]]:
        all_records = []

        for query_input in raw_inputs:
            industry = query_input.keyword or query_input.industry or ""
            city = query_input.location or "kolkata"

            self.logger.info(f"Running directory discovery for: {industry} in {city}")

            seeds, mode = await discover_seeds(
                industry=industry,
                cities=[city],
                max_results=50,
            )

            self.logger.info(
                f"Directory discovery found {len(seeds)} seeds (mode: {mode})"
            )

            records = seeds_to_records(seeds)
            all_records.extend(records)

        return all_records

    def run(self) -> None:
        raw_inputs = self._load_input_queries()
        if not raw_inputs:
            return

        raw_records: List[Dict[str, Any]] = []

        indian_sme_inputs = [q for q in raw_inputs if self._is_indian_sme_query(q)]

        if indian_sme_inputs:
            self.logger.info(
                f"Running directory-first discovery for {len(indian_sme_inputs)} Indian SME queries"
            )
            raw_records = asyncio.run(self._run_directory_discovery(indian_sme_inputs))

        non_indian_inputs = [q for q in raw_inputs if q not in indian_sme_inputs]
        if non_indian_inputs:
            search_queries = build_queries(non_indian_inputs)
            jobs = self.job_manager.build_jobs(search_queries)
            scheduled = self.scheduler.schedule(jobs)

            self.logger.info(
                f"Running scraper engine for {len(scheduled)} jobs / queries."
            )
            queries = [j.query for j in scheduled]

            scraper_result = asyncio.run(self.engine.run_async(queries))
            raw_records.extend(scraper_result.records)

        self.logger.info(f"Collected {len(raw_records)} raw records total.")

        final_records = self.pipeline.run(raw_records)
        self.logger.info(f"Pipeline produced {len(final_records)} final records.")

        json_path = self.project_root / "output" / "results.json"
        csv_path = self.project_root / "output" / "results.csv"
        write_json(json_path, final_records)
        write_csv(csv_path, final_records)

        creds_path = self.project_root / "credentials" / "google_credentials.json"
        try:
            append_to_sheet(
                credentials_path=creds_path,
                sheet_name=self.settings.google_sheet_name,
                worksheet_name=self.settings.google_worksheet_name,
                records=final_records,
            )
        except Exception as exc:
            self.logger.warning(f"Google Sheets append failed: {exc}")
