from __future__ import annotations

from typing import Any, Dict, Iterable, List

from processors.cleaner import clean_record
from processors.normalizer import normalize_record
from processors.company_enrichment import enrich_company
from processors.deduplicator import deduplicate
from processors.advanced_cleaner import clean_and_filter
from extractors.location_parser import enrich_record_with_location
from utils.schema_formatter import to_output_schema


class Pipeline:
    def run(self, raw_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raw_list = list(raw_records)

        cleaned = clean_and_filter(raw_list)

        normalized = [normalize_record(r) for r in cleaned]
        enriched = [enrich_company(r) for r in normalized]
        with_locations = [enrich_record_with_location(r) for r in enriched]
        unique = deduplicate(with_locations)
        return to_output_schema(unique)
