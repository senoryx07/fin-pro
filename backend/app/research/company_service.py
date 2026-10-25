from sqlmodel import Session, select

from backend.app.models.company import (
    Company,
    CompanyResponse,
    SecurityResponse,
)
from backend.app.models.security import Security


def build_company_response(
    company: Company,
    security: Security,
) -> CompanyResponse:
    return CompanyResponse(
        name=company.name,
        sector=company.sector,
        industry=company.industry,
        description=company.description,
        security=SecurityResponse(
            ticker=security.ticker,
            exchange=security.exchange,
            isin=security.isin,
            security_type=security.security_type,
            series=security.series,
            exchange_code=security.exchange_code,
            status=security.status,
        ),
    )


def search_companies(
    session: Session,
    query: str,
) -> list[CompanyResponse]:
    query = query.strip().lower()

    if not query:
        return []

    companies = session.exec(
        select(Company)
    ).all()

    securities = session.exec(
        select(Security).where(
            Security.exchange == "NSE"
        )
    ).all()

    security_by_company: dict[
        int,
        Security,
    ] = {}

    for security in securities:
        security_by_company[
            security.company_id
        ] = security

    results: list[CompanyResponse] = []

    for company in companies:
        if company.id is None:
            continue

        security = security_by_company.get(
            company.id
        )

        if security is None:
            continue

        ticker_matches = (
            security.ticker is not None
            and query in security.ticker.lower()
        )

        if (
            query in company.name.lower()
            or query in company.sector.lower()
            or query in company.industry.lower()
            or ticker_matches
        ):
            results.append(
                build_company_response(
                    company=company,
                    security=security,
                )
            )

    return results


def get_company_by_ticker(
    session: Session,
    ticker: str,
) -> CompanyResponse | None:
    ticker = ticker.strip().upper()

    security = session.exec(
        select(Security).where(
            Security.ticker == ticker,
            Security.exchange == "NSE",
        )
    ).first()

    if security is None:
        return None

    company = session.exec(
        select(Company).where(
            Company.id == security.company_id
        )
    ).first()

    if company is None:
        return None

    return build_company_response(
        company=company,
        security=security,
    )