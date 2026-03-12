# DataHarvester – Multi-Platform Company Data Scraper

DataHarvester is a modular, extensible Python 3.10+ framework for discovering and enriching company data globally from multiple online sources, and exporting the results to Google Sheets, JSON, and CSV.

## Features

- **Global company discovery** from Google Search, Google Maps, LinkedIn, and company websites.
- **Pluggable scrapers** with a shared base class for fast extension.
- **Contact extraction** for emails, phones, addresses, and leadership.
- **Processing pipeline** for cleaning, normalization, enrichment, and deduplication.
- **Structured output schema** suitable for CRM / ERP lead ingestion.
- **Storage backends** for Google Sheets, JSON, and CSV.
- **Logging and error tracking** via `loguru`.

## Installation

```bash
pip install -r requirements.txt
python -m playwright install
```

## Quick Start

1. Populate input queries in `input/queries.csv` using the format:

```text
keyword,location,industry
erp companies,,software
sap partners,,erp
logistics companies,,logistics
manufacturing companies,germany,manufacturing
tech startups,,technology
```

2. Add your Google service account credentials JSON to `credentials/google_credentials.json`.

3. Adjust platform and proxy settings in `config/platforms.yaml` and `config/proxies.yaml`.

4. Run the main controller:

```bash
python main.py
```

The system will:

1. Load input queries.
2. Generate global and (optional) location-specific search phrases.
3. Run the scraper engine (async) across enabled platforms.
4. Process and normalize data through the pipeline.
5. Deduplicate and map records to the final schema.
6. Save results to `output/results.json`, `output/results.csv`, and Google Sheets.

## Data Source Behavior (Important)

By default, the API now serves **live scraped results only** (from `output/results.json`) and does **not** preload `data.json` seed records.

If you want to include `data.json` as startup seed data, set:

```bash
export DATAHARVESTER_USE_SEED_DATA=true
```

## Notes

- This project ships with conservative default scrapers and HTML parsing logic. Many sites change their structure often; you may need to adjust individual scraper implementations and respect each site's terms of service and robots.txt.
- For production use, configure robust proxy management and rate limiting in `utils/proxy_manager.py` and `utils/rate_limiter.py`.

