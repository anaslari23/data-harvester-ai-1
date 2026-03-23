from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterable, List

from processors.cleaner import clean_record
from processors.normalizer import normalize_record
from processors.company_enrichment import enrich_company
from processors.deduplicator import deduplicate
from processors.advanced_cleaner import clean_and_filter
from processors.external_enrichment import (
    enrich_record_sync,
    enrich_with_external_sources,
)
from extractors.location_parser import enrich_record_with_location
from extractors.rule_extractor import (
    extract_company_name,
    extract_employee_count,
    extract_turnover,
    extract_erp_from_text,
)
from utils.schema_formatter import to_output_schema


class Pipeline:
    def run(self, raw_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raw_list = list(raw_records)

        cleaned = clean_and_filter(raw_list)

        normalized = [normalize_record(r) for r in cleaned]

        normalized = self._clean_company_names(normalized)

        enriched = [enrich_company(r) for r in normalized]

        enriched = [enrich_record_sync(r) for r in enriched]

        with_locations = [enrich_record_with_location(r) for r in enriched]
        unique = deduplicate(with_locations)
        return to_output_schema(unique)

    def _clean_company_names(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Clean company names using rule_extractor."""
        from bs4 import BeautifulSoup

        cleaned = []
        for rec in records:
            rec = dict(rec)

            if rec.get("company_name"):
                name = rec["company_name"]

                if name and len(name) > 60:
                    html = rec.get("description", "") + rec.get("additional_info", "")
                    if html:
                        try:
                            soup = BeautifulSoup(html, "lxml")
                            clean_name = extract_company_name(soup)
                            if clean_name and len(clean_name) < 60:
                                rec["company_name"] = clean_name
                        except Exception:
                            pass

            cleaned.append(rec)

        return cleaned

    async def run_async(
        self, raw_records: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Async version with external enrichment."""
        raw_list = list(raw_records)

        cleaned = clean_and_filter(raw_list)

        normalized = [normalize_record(r) for r in cleaned]

        normalized = self._clean_company_names(normalized)

        enriched = [enrich_company(r) for r in normalized]

        enriched = [enrich_record_sync(r) for r in enriched]

        enriched = await enrich_with_external_sources(enriched)

        with_locations = [enrich_record_with_location(r) for r in enriched]
        unique = deduplicate(with_locations)
        return to_output_schema(unique)
