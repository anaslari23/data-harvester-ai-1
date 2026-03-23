from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List

from extractors.mca_api import enrich_with_mca
from extractors.wikipedia_enricher import enrich_with_wikipedia
from extractors.ddg_knowledge import enrich_with_ddg
from extractors.naukri_erp import detect_erp
from extractors.indiamart_profile import enrich_with_indiamart
from extractors.tradeindia_profile import enrich_with_tradeindia
from extractors.gstin_lookup import enrich_with_gstin, GSTINLookup
from extractors.rule_extractor import (
    extract_employee_count,
    extract_turnover,
    extract_erp_from_text,
)


async def enrich_with_external_sources(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Enrich records with external data sources in priority order:
    1. IndiaMart (best for small Indian manufacturers)
    2. TradeIndia (secondary SME source)
    3. GSTIN lookup (if GSTIN found)
    4. DDG Knowledge Panel
    5. Wikipedia (for larger companies)
    6. Naukri ERP detection
    """
    enriched_records = []
    gstin_lookup = GSTINLookup()

    for record in records:
        rec = dict(record)
        company_name = rec.get("company_name", "")

        if not company_name or len(company_name) < 3:
            enriched_records.append(rec)
            continue

        company_name_clean = company_name.strip()

        if not rec.get("contact_name") or not rec.get("turnover"):
            rec = await enrich_with_indiamart(company_name_clean, rec)
            await asyncio.sleep(0.5)

        if not rec.get("contact_name") or not rec.get("turnover"):
            rec = await enrich_with_tradeindia(company_name_clean, rec)
            await asyncio.sleep(0.5)

        gstin_text = str(rec.get("additional_info", ""))
        gstin = gstin_lookup.extract_gstin_from_text(gstin_text)
        if gstin:
            rec = await enrich_with_gstin(gstin, rec)
            await asyncio.sleep(0.5)

        rec = await enrich_with_ddg(company_name_clean, rec)
        await asyncio.sleep(0.3)

        rec = await enrich_with_wikipedia(company_name_clean, rec)
        await asyncio.sleep(0.3)

        if not rec.get("contact_name"):
            try:
                rec = await enrich_with_mca(company_name_clean, rec)
            except Exception:
                pass

        if not rec.get("erp_software"):
            combined = " ".join(
                [
                    str(rec.get("description", "")),
                    str(rec.get("additional_info", "")),
                ]
            )
            erp_from_text = extract_erp_from_text(combined)
            if erp_from_text:
                rec["erp_software"] = erp_from_text

            try:
                erp_from_naukri = await detect_erp(company_name_clean)
                if erp_from_naukri:
                    rec["erp_software"] = erp_from_naukri
            except Exception:
                pass

        enriched_records.append(rec)

        await asyncio.sleep(0.5)

    return enriched_records


def enrich_record_sync(record: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous enrichment using regex patterns only."""
    rec = dict(record)

    combined_text = " ".join(
        [
            str(rec.get("description", "")),
            str(rec.get("additional_info", "")),
            str(rec.get("company_name", "")),
        ]
    )

    if not rec.get("employee_count"):
        emp = extract_employee_count(combined_text)
        if emp:
            rec["employee_count"] = emp

    if not rec.get("turnover"):
        turn = extract_turnover(combined_text)
        if turn:
            rec["turnover"] = turn

    if not rec.get("erp_software"):
        erp = extract_erp_from_text(combined_text)
        if erp:
            rec["erp_software"] = erp

    return rec
