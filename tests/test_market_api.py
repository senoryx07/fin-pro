from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from backend.app.database.database import get_session
from backend.app.main import app
from backend.app.models.company import Company
from backend.app.models.financials import FinancialResult
from backend.app.models.market_data import DailyPrice
from backend.app.models.security import Security


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(
            name="Test Industries",
            sector="Industrials",
            industry="Machinery",
            description="Test company",
        )
        session.add(company)
        session.commit()

        security = Security(
            company_id=company.id,
            ticker="TEST",
            exchange="NSE",
            series="EQ",
        )
        session.add(security)
        session.commit()

        start = date(2026, 1, 1)

        for day in range(30):
            close = 100.0 + day
            session.add(
                DailyPrice(
                    security_id=security.id,
                    trade_date=start + timedelta(days=day),
                    open=close - 0.5,
                    high=close + 1,
                    low=close - 1,
                    close=close,
                    previous_close=close - 1,
                    volume=1000 + day,
                )
            )

        session.commit()

        quarter_ends = [
            date(2025, 3, 31),
            date(2025, 6, 30),
            date(2025, 9, 30),
            date(2025, 12, 31),
        ]

        for end in quarter_ends:
            session.add(
                FinancialResult(
                    security_id=security.id,
                    period_start=end.replace(day=1) - timedelta(days=60),
                    period_end=end,
                    consolidated=True,
                    revenue=1000.0,
                    expenses=800.0,
                    net_profit_owners=50.0,
                    paid_up_capital=1000.0,
                    face_value=10.0,
                )
            )

        session.commit()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session

    # Not used as a context manager, so the lifespan (which seeds the real
    # database) does not run.
    yield TestClient(app)

    app.dependency_overrides.clear()


def test_prices_are_ordered_and_limited(client):
    response = client.get("/api/companies/test/prices?limit=5")

    assert response.status_code == 200

    points = response.json()["points"]

    assert len(points) == 5
    assert points[-1]["trade_date"] == "2026-01-30"
    assert points[0]["trade_date"] == "2026-01-26"
    # SMA 20 of a +1/day series ending at 129 is 119.5.
    assert points[-1]["sma_20"] == pytest.approx(119.5)


def test_technical_snapshot(client):
    response = client.get("/api/companies/TEST/technicals")

    assert response.status_code == 200

    data = response.json()

    assert data["sessions"] == 30
    assert data["last_close"] == 129.0
    assert data["change"] == pytest.approx(1.0)
    assert data["period_high"] == 130.0
    assert data["period_low"] == 99.0
    assert data["rsi_14"] == 100.0
    assert data["macd"] is not None
    assert data["macd_signal"] is None
    assert data["returns"]["1W"] == pytest.approx(129 / 124 - 1)
    assert data["returns"]["1Y"] is None

    sma_20 = data["moving_averages"][0]

    assert sma_20["period"] == 20
    assert sma_20["price_above_sma"] is True


def test_unknown_ticker_returns_404(client):
    assert client.get("/api/companies/NOPE/prices").status_code == 404
    assert client.get("/api/companies/NOPE/technicals").status_code == 404


def test_fundamentals_and_valuation(client):
    fundamentals = client.get("/api/companies/TEST/fundamentals").json()

    assert fundamentals["basis"] == "consolidated"
    assert fundamentals["shares_outstanding"] == 100
    assert fundamentals["ttm_net_profit"] == 200
    assert fundamentals["ttm_eps"] == 2
    assert len(fundamentals["quarters"]) == 4

    valuation = client.get("/api/companies/TEST/valuation").json()

    assert valuation["price"] == 129.0
    assert valuation["market_cap"] == 12900
    assert valuation["pe_ratio"] == 64.5
    assert valuation["price_to_sales"] == pytest.approx(12900 / 4000)


def test_fundamentals_rejects_unknown_basis(client):
    response = client.get("/api/companies/TEST/fundamentals?basis=other")

    assert response.status_code == 422
