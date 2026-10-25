from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.app.database.database import get_session
from backend.app.models.company import CompanyResponse
from backend.app.research.company_service import (
    get_company_by_ticker,
    search_companies,
)


router = APIRouter(
    prefix="/api/companies",
    tags=["Companies"],
)


@router.get(
    "/search",
    response_model=list[CompanyResponse],
)
def search_company(
    q: str = Query(
        ...,
        min_length=1,
        description=(
            "Company name, ticker, sector or industry"
        ),
    ),
    session: Session = Depends(get_session),
):
    return search_companies(
        session=session,
        query=q,
    )


@router.get(
    "/{ticker}",
    response_model=CompanyResponse,
)
def get_company(
    ticker: str,
    session: Session = Depends(get_session),
):
    company = get_company_by_ticker(
        session=session,
        ticker=ticker,
    )

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    return company