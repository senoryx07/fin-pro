"""
Assign sectors and industries from NSE index constituent lists.

    python -m backend.app.ingestion.classification_loader

The "Industry" column of the Nifty Total Market and Microcap lists becomes
both sector and industry, so peer groups stay consistent. Financial
Services is split into Banks (banking-format filers, or "Bank" in the
name) and everything else.
"""

import io
import time

import pandas as pd
import requests
from sqlmodel import Session, select

from backend.app.database.database import engine
from backend.app.models.company import Company
from backend.app.models.financials import FinancialResult
from backend.app.models.security import Security


INDEX_URL = "https://nsearchives.nseindia.com/content/indices/{name}.csv"

BROAD_LISTS = (
    "ind_niftytotalmarket_list",
    "ind_niftymicrocap250_list",
)

def download_list(
    session: requests.Session,
    name: str,
) -> pd.DataFrame:
    response = session.get(INDEX_URL.format(name=name), timeout=30)
    response.raise_for_status()

    time.sleep(0.5)

    return pd.read_csv(io.StringIO(response.text))


def load_classification() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/154.0 Safari/537.36"
            ),
        }
    )

    sectors: dict[str, str] = {}

    for name in BROAD_LISTS:
        for row in download_list(session, name).itertuples():
            sectors.setdefault(row.Symbol.strip().upper(), row.Industry.strip())

    with Session(engine) as db:
        banks = set(
            db.exec(
                select(FinancialResult.security_id)
                .where(FinancialResult.is_bank)
                .distinct()
            ).all()
        )

        rows = db.exec(
            select(Company, Security)
            .join(Security, Security.company_id == Company.id)
            .where(Security.exchange == "NSE")
        ).all()

        updated = 0

        for company, security in rows:
            ticker = (security.ticker or "").upper()
            sector = sectors.get(ticker)

            if sector is None:
                # Keep any existing classification for companies outside
                # the index lists.
                continue

            industry = sector

            if sector == "Financial Services" and (
                security.id in banks or " bank" in company.name.lower()
            ):
                industry = "Banks"

            if (company.sector, company.industry) != (sector, industry):
                company.sector = sector
                company.industry = industry
                db.add(company)
                updated += 1

        db.commit()

    print(
        f"Classified {len(sectors)} NSE symbols; "
        f"updated {updated} companies."
    )


if __name__ == "__main__":
    load_classification()
