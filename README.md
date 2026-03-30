# DataHarvester AI – Multi-Platform Company Data Scraper

DataHarvester is a modular, extensible Python 3.10+ framework for discovering and enriching company data globally from multiple online sources, and exporting the results to Google Sheets, JSON, CSV, and Supabase.

## Features

- **Natural language queries** — type "toys manufacturer in kolkata, india" and the system automatically parses keyword, location, and country.
- **13+ platform scrapers** — Google/DuckDuckGo, LinkedIn, Google Maps, IndiaMart, TradeIndia, JustDial, Clutch, GoodFirms, Exporters India, and more.
- **JSON-LD / Schema.org extraction** — structured data from company websites yields high-fidelity names, contacts, addresses, and employee counts.
- **Multi-page crawling** — automatically visits About, Team, Leadership, and Contact pages to find decision-maker names.
- **Decision-maker extraction** — recognises CEO, CTO, CFO, IT Head, Finance Head, Managing Director, Owner, Founder, and more.
- **Smart search queries** — builds contact-oriented and site-specific dork variants for each query (e.g. `site:indiamart.com`).
- **Processing pipeline** — cleaning, normalization, company enrichment, external API enrichment (IndiaMart, TradeIndia, GSTIN, MCA, Wikipedia, Naukri), location parsing, and fuzzy deduplication.
- **Structured output schema** suitable for CRM / ERP lead ingestion.
- **Storage backends** — Google Sheets, JSON, CSV, and Supabase (PostgreSQL).
- **REST API + React UI** — FastAPI backend with a Next.js frontend for browser-based scraping.

## Output Schema

Every record is mapped to the following fields:

| # | Field | Description |
|---|-------|-------------|
| 1 | SL No. | Auto-generated serial number |
| 2 | Company Name | Legal / trading name |
| 3 | Website | Company URL |
| 4 | Owner / IT Head / CEO / Finance Head Name | Decision-maker contact name |
| 5 | Phone Number | Primary phone (normalised) |
| 6 | EMail Address | Business email (validated) |
| 7 | Address | Full postal address |
| 8 | Industry_Type | Inferred industry category |
| 9 | Employee_No | Employee count / band |
| 10 | Branch / Warehouse_No | Number of branches / offices |
| 11 | Annual_Turnover | Revenue (formatted, e.g. "Rs. 5 Crore") |
| 12 | Current_Use_ERP Software_Name | Detected ERP (SAP, Tally, Zoho, etc.) |
| 13 | Additional_Information | Source attribution and extra context |

## Installation

```bash
pip install -r requirements.txt
python -m playwright install
```

## Quick Start

### Option A — REST API (recommended)

```bash
# Start the backend
python run_backend.py          # → http://localhost:8000

# Start the frontend (optional)
cd frontend && npm install && npm run dev   # → http://localhost:3000
```

Then call the API:

```bash
curl -X POST http://localhost:8000/api/start-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "toys manufacturer in kolkata, india",
    "sources": ["google", "indiamart", "tradeindia", "justdial", "linkedin", "website"]
  }'
```

The system automatically parses the natural language keyword into structured fields and runs all enabled scrapers.

### Option B — CLI

1. Populate `input/queries.csv`:

```text
keyword,location,industry
toys manufacturer,kolkata,
steel suppliers,mumbai,manufacturing
erp companies,,software
```

2. Run:

```bash
python main.py
```

Results are saved to `output/results.json` and `output/results.csv`.

## Configuration

### Platform toggles (`config/platforms.yaml`)

```yaml
discovery: true        # Directory-first discovery for Indian SMEs
website: true          # Deep-scrape company websites
direct_website: true   # Construct URLs from company names as fallback
google: true           # DuckDuckGo search
linkedin: true         # LinkedIn company pages
indiamart: true        # India B2B directory
tradeindia: true       # India B2B directory
justdial: true         # India business directory
```

### Environment variables

Copy `env.template` to `.env` and fill in:

```
FIRECRAWL_API_KEY=...              # Optional: Firecrawl web scraping
GOOGLE_PLACES_API_KEY=...          # Optional: Google Places API
GOOGLE_SEARCH_API_KEY=...          # Optional: Google Search API
GOOGLE_SEARCH_ENGINE_ID=...        # Optional: Custom search engine
```

### Proxy configuration (`config/proxies.yaml`)

Supports pool, Webshare, Bright Data, SmartProxy, and custom modes with round-robin or random rotation.

## How It Works

```
Natural language query (e.g. "toys manufacturer in kolkata, india")
  │
  ├─ NL Parser → keyword="toys manufacturer", location="kolkata"
  │
  ├─ Query Builder → ["toys manufacturer kolkata",
  │                    "toys manufacturer kolkata contact email phone",
  │                    "site:indiamart.com toys manufacturer kolkata", ...]
  │
  ├─ Scraper Engine (async, concurrent)
  │   ├─ Google/DDG → 15 results per variant, deep-enriched
  │   ├─ IndiaMart → company profiles with contact person + turnover
  │   ├─ TradeIndia → fallback B2B directory
  │   ├─ JustDial → phone + address rich
  │   ├─ LinkedIn → company pages + key people
  │   ├─ Website scraper → homepage + about/team/contact pages
  │   └─ JSON-LD extraction on every fetched page
  │
  ├─ Processing Pipeline
  │   ├─ Clean & filter (HTML, spam, validation)
  │   ├─ Normalize (emails, phones, URLs, names)
  │   ├─ Company enrichment (industry, employee count, turnover, branch count, ERP, contact name)
  │   ├─ External enrichment (IndiaMart → TradeIndia → GSTIN → MCA → Wikipedia → Naukri)
  │   ├─ Location parsing (city/state/country from address)
  │   └─ Fuzzy deduplication (Levenshtein, threshold 0.85)
  │
  └─ Output
      ├─ output/results.json
      ├─ output/results.csv
      ├─ Google Sheets (optional)
      └─ Supabase (optional)
```

## Data Source Behavior

By default, the API serves **live scraped results only** and does **not** preload seed data.

To include `data.json` as startup seed data:

```bash
export DATAHARVESTER_USE_SEED_DATA=true
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Docker, Render, Railway, and Netlify deployment guides.

## Notes

- This project ships with conservative default scrapers and HTML parsing logic. Sites change structure often; you may need to adjust individual scraper implementations.
- Always respect each site's terms of service and robots.txt.
- For production use, configure robust proxy management and rate limiting.
