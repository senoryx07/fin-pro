# Fin Pro

## Financial Research & Analytics Platform

Fin Pro is a research website for Indian listed equities. Search any
NSE-listed company and get its price history, quarterly results, valuation
and technical analysis in one place.

## How it works

Fin Pro is a **static website**, so it can be hosted free on GitHub Pages,
Cloudflare Pages, Netlify or Vercel with no server.

```
NSE (bhavcopy + XBRL results)
   │  Python pipeline (backend/)
   ▼
finpro.db (SQLite, local only)
   │  python -m backend.app.update
   ▼
frontend/public/data/*.json   ← one file per company + search index
   │  npm run build
   ▼
frontend/dist                 ← the website, deployable anywhere
```

- **Pipeline:** Python, SQLModel, SQLite, pandas
- **Website:** React 19, TypeScript, Vite (hash routes such as
  `#/research/TCS/valuation`, so no server rewrites are needed)
- **Data:** NSE security master, NSE daily bhavcopy prices, and NSE
  quarterly results filings (XBRL), adjusted for splits and bonuses

## Getting Started

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

cd frontend
npm install
```

### First-time data load

```bash
python -m backend.app.ingestion.nse_security_loader          # company list
python -m backend.app.ingestion.market_loader --start 2025-10-01
python -m backend.app.ingestion.financial_loader --top 100   # results, ~1 min/company
```

### Daily update

```bash
python -m backend.app.update            # new prices + results, then export JSON
python -m backend.app.update --top 200  # also add results for more companies
```

### Run the website locally

```bash
cd frontend
npm run dev                             # http://localhost:5173
```

### Tests

```bash
pytest
```

## Deploying

The generated data (~45 MB) is **not committed**; it changes daily and would
bloat the repository. Deploy the built site instead.

**GitHub Pages**

1. Push this repository to GitHub.
2. Run `python scripts/deploy.py`. It builds the site and force-pushes it to
   a `gh-pages` branch as a single commit (no history builds up).
3. In the repository settings, under **Pages**, set the source to the
   `gh-pages` branch.

**Cloudflare Pages** (free, no bandwidth cap)

```bash
cd frontend
npm run build
npx wrangler pages deploy dist --project-name fin-pro
```

Re-run the update and the deploy step whenever you want fresh data.

## Local API (optional)

The FastAPI app exposes the same data for development:
`uvicorn backend.app.main:app --reload`, then open
http://127.0.0.1:8000/docs.

## Research Modules

| Module | Status |
| --- | --- |
| Company Overview | ✅ Live |
| Fundamentals (quarterly & annual results) | ✅ Live |
| Valuation (market cap, P/E, P/S, P/E history) | ✅ Live |
| Technical Analysis | ✅ Live |
| Markets (all companies, sortable) | ✅ Live |
| Peer Comparison | Planned |
| News & Filings | Planned |
| Business, Management, Industry | Planned |

Not investment advice.
