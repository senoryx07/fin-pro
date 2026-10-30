from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.app.database.database import get_session
from backend.app.financials.service import build_fundamentals
from backend.app.models.financials import (
    FundamentalsResponse,
    ValuationResponse,
)
from backend.app.technicals.service import find_nse_security
from backend.app.valuation.service import build_valuation


router = APIRouter(
    prefix="/api/companies",
    tags=["Fundamentals"],
)

Basis = Literal["consolidated", "standalone"]


@router.get(
    "/{ticker}/fundamentals",
    response_model=FundamentalsResponse,
)
def get_fundamentals(
    ticker: str,
    basis: Basis | None = Query(default=None),
    session: Session = Depends(get_session),
):
    security = find_nse_security(session, ticker)

    if security is None:
        raise HTTPException(
            status_code=404,
            detail="Security not found",
        )

    return build_fundamentals(
        session=session,
        security=security,
        basis=basis,
    )


@router.get(
    "/{ticker}/valuation",
    response_model=ValuationResponse,
)
def get_valuation(
    ticker: str,
    basis: Basis | None = Query(default=None),
    session: Session = Depends(get_session),
):
    security = find_nse_security(session, ticker)

    if security is None:
        raise HTTPException(
            status_code=404,
            detail="Security not found",
        )

    return build_valuation(
        session=session,
        security=security,
        basis=basis,
    )
