# Fin Pro

## Financial Research & Analytics Platform

Fin Pro is a research workspace for Indian listed equities. Search a company
and get its profile, price history and technical analysis in one place, with
fundamentals, valuation and peer modules to follow.

## Stack

- **Backend:** Python, FastAPI, SQLModel, SQLite (`finpro.db`)
- **Frontend:** React 19, TypeScript, Vite
- **Data:** NSE / BSE security masters and NSE daily bhavcopy prices

## Getting Started

```bash
# Backend (from the project root)
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn backend.app.main:app --reload     # http://127.0.0.1:8000/docs

# Frontend
cd frontend
npm install
npm run dev                               # http://localhost:5173
```

### Loading data

```bash
python -m backend.app.ingestion.nse_security_loader   # NSE security master
python -m backend.app.ingestion.bse_security_loader   # BSE security master
python -m backend.app.ingestion.market_loader         # NSE daily price backfill
```

Edit the date range at the bottom of `market_loader.py` to backfill more
history. MACD needs 34 sessions, SMA 50 needs 50 and SMA 200 needs 200; the
Technicals tab shows which indicators are waiting on data.

### Tests

```bash
pytest
```

## API

| Endpoint | Description |
| --- | --- |
| `GET /api/companies/search?q=` | Search by name, ticker, sector or industry |
| `GET /api/companies/{ticker}` | Company profile and NSE listing |
| `GET /api/companies/{ticker}/prices?limit=` | Daily OHLCV with SMA 20 and Bollinger bands |
| `GET /api/companies/{ticker}/technicals` | RSI, MACD, moving averages, returns, volatility |
| `GET /api/securities` / `{ticker}` | Raw security master |

## Research Modules

| Module | Status |
| --- | --- |
| Company Overview | ✅ Live |
| Technical Analysis | ✅ Live |
| Business & Operating Segments | Planned |
| Management & Founders | Planned |
| Industry Analysis | Planned |
| Fundamental Analysis | Planned (needs a financial-statements source) |
| Valuation Analysis | Planned |
| Peer Comparison | Planned |
| News & Events | Planned |
| Filings & Reports | Planned |

## Project Status

🚧 Under Development
