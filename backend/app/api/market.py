from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.app.database.database import get_session
from backend.app.models.market_data import (
    PriceSeriesResponse,
    TechnicalSnapshot,
)
from backend.app.technicals.service import (
    build_price_series,
    build_technical_snapshot,
)


router = APIRouter(
    prefix="/api/companies",
    tags=["Market Data"],
)


@router.get(
    "/{ticker}/prices",
    response_model=PriceSeriesResponse,
)
def get_prices(
    ticker: str,
    limit: int | None = Query(
        default=None,
        ge=1,
        le=5000,
        description="Return only the latest N sessions",
    ),
    session: Session = Depends(get_session),
):
    series = build_price_series(
        session=session,
        ticker=ticker,
        limit=limit,
    )

    if series is None:
        raise HTTPException(
            status_code=404,
            detail="Security not found",
        )

    return series


@router.get(
    "/{ticker}/technicals",
    response_model=TechnicalSnapshot,
)
def get_technicals(
    ticker: str,
    session: Session = Depends(get_session),
):
    snapshot = build_technical_snapshot(
        session=session,
        ticker=ticker,
    )

    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail="Security not found",
        )

    return snapshot
