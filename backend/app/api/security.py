from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from backend.app.database.database import get_session
from backend.app.models.security import Security


router = APIRouter(
    prefix="/api/securities",
    tags=["Securities"],
)


@router.get("")
def list_securities(
    session: Session = Depends(get_session),
):
    statement = select(Security)

    securities = session.exec(statement).all()

    return {
        "count": len(securities),
        "results": securities,
    }


@router.get("/{ticker}")
def get_security(
    ticker: str,
    session: Session = Depends(get_session),
):
    statement = select(Security).where(
        Security.ticker == ticker.upper()
    )

    security = session.exec(statement).first()

    if security is None:
        raise HTTPException(
            status_code=404,
            detail="Security not found",
        )

    return security