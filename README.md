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
python -m backend.app.ingestion.classification_loader        # sectors
python -m backend.app.ingestion.financial_loader --top 100   # results, ~1 min/company
python -m backend.app.ingestion.corporate_loader --top 800   # shareholding, announcements
```

### Daily update

```bash
python -m backend.app.update            # prices, results, announcements, export
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

The site is hosted on **GitHub Pages** from the `gh-pages` branch and
updates itself.

**Automatic daily update (GitHub Actions)**

`.github/workflows/daily-update.yml` runs every weekday at 19:30 IST:

1. restores the database from the `db-latest` release (or `seed/` on the
   very first run),
2. runs `python -m backend.app.update` against NSE,
3. saves the database back to the `db-latest` release,
4. builds the site and publishes it to `gh-pages` as a single commit.

Run it on demand from the repository's **Actions** tab ("Daily data update"
→ **Run workflow**). The generated site data (~50 MB) is never committed to
`master`, and `gh-pages` keeps no history, so the repository stays small.

**Manual deploy** (from your own machine)

```bash
python -m backend.app.update
python scripts/deploy.py      # force-pushes the build to gh-pages
```

`scripts/install_schedule.ps1` sets up the same nightly job with Windows
Task Scheduler, if you'd rather run it locally.

## Local API (optional)

The FastAPI app exposes the same data for development:
`uvicorn backend.app.main:app --reload`, then open
http://127.0.0.1:8000/docs.

## Research Modules

| Tab | What it shows | Source |
| --- | --- | --- |
| Overview | Quote, price chart, company snapshot, key metrics | NSE bhavcopy |
| Fundamentals | Quarterly & annual results, margins, growth | NSE results XBRL |
| Valuation | Market cap, P/E, P/S, P/E history | Prices + results |
| Technicals | RSI, MACD, Bollinger, moving averages, returns | NSE bhavcopy |
| Peers | Largest companies in the same industry | NSE index lists |
| Shareholding | Promoter vs public holding by quarter | NSE |
| Announcements | Filings, corporate actions, board meetings | NSE |

Results, shareholding and announcements cover the most-traded companies;
prices and technicals cover every NSE equity.

Not investment advice.
