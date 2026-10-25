from sqlmodel import Session, select

from backend.app.database.database import engine
from backend.app.models.company import Company
from backend.app.models.security import Security
from backend.app.providers.nse_security_data import (
    NSESecurityProvider,
)


def normalize_name(name: str) -> str:
    return (
        name.strip()
        .upper()
        .replace("LIMITED", "")
        .replace("LTD.", "")
        .replace("LTD", "")
        .replace("PRIVATE", "")
        .replace("PVT.", "")
        .replace("PVT", "")
        .replace(".", "")
        .replace(",", "")
        .replace("&", "AND")
        .replace("  ", " ")
        .strip()
    )


def find_existing_company(
    session: Session,
    security_data: dict,
) -> Company | None:
    isin = security_data.get("isin")

    if isin:
        existing_security = session.exec(
            select(Security).where(
                Security.isin == isin,
            )
        ).first()

        if existing_security:
            return session.exec(
                select(Company).where(
                    Company.id == existing_security.company_id
                )
            ).first()

    normalized_name = normalize_name(
        security_data["name"]
    )

    companies = session.exec(
        select(Company)
    ).all()

    for company in companies:
        if normalize_name(company.name) == normalized_name:
            return company

    return None


def find_existing_security(
    session: Session,
    ticker: str,
) -> Security | None:
    return session.exec(
        select(Security).where(
            Security.ticker == ticker,
            Security.exchange == "NSE",
        )
    ).first()


def load_nse_security_master() -> None:
    provider = NSESecurityProvider()

    print()
    print("========================================")
    print("FIN PRO - NSE SECURITY MASTER IMPORT")
    print("========================================")
    print()

    print("Downloading official NSE security master...")

    securities = provider.get_security_master()

    print(
        f"NSE returned {len(securities)} security records."
    )

    created_companies = 0
    updated_companies = 0
    inserted_securities = 0
    updated_securities = 0
    skipped_securities = 0

    with Session(engine) as session:

        for security_data in securities:

            ticker = security_data.get(
                "ticker"
            )

            name = security_data.get(
                "name"
            )

            isin = security_data.get(
                "isin"
            )

            if not ticker or not name:
                skipped_securities += 1
                continue

            existing_security = find_existing_security(
                session=session,
                ticker=ticker,
            )

            if existing_security:

                existing_security.isin = (
                    isin
                )

                existing_security.series = (
                    security_data.get(
                        "series"
                    )
                )

                existing_security.security_type = (
                    security_data.get(
                        "security_type",
                        "EQUITY",
                    )
                )

                existing_security.status = (
                    security_data.get(
                        "status",
                        "ACTIVE",
                    )
                )

                session.add(
                    existing_security
                )

                updated_securities += 1

                continue

            company = find_existing_company(
                session=session,
                security_data=security_data,
            )

            if company is None:

                company = Company(
                    name=name,
                    sector="Unclassified",
                    industry="Unclassified",
                    description=(
                        "Company profile pending "
                        "enrichment from Fin Pro "
                        "research data sources."
                    ),
                )

                session.add(company)
                session.flush()

                created_companies += 1

            else:
                updated_companies += 1

            new_security = Security(
                company_id=company.id,
                ticker=ticker,
                isin=isin,
                exchange="NSE",
                security_type=security_data.get(
                    "security_type",
                    "EQUITY",
                ),
                series=security_data.get(
                    "series"
                ),
                exchange_code=None,
                status=security_data.get(
                    "status",
                    "ACTIVE",
                ),
            )

            session.add(
                new_security
            )

            inserted_securities += 1

        session.commit()

    print()
    print("========================================")
    print("NSE IMPORT COMPLETE")
    print("========================================")
    print(
        f"Companies created:       {created_companies}"
    )
    print(
        f"Companies matched:       {updated_companies}"
    )
    print(
        f"Securities inserted:     {inserted_securities}"
    )
    print(
        f"Securities updated:      {updated_securities}"
    )
    print(
        f"Records skipped:         {skipped_securities}"
    )
    print(
        f"Total NSE records:       {len(securities)}"
    )
    print("========================================")
    print()


if __name__ == "__main__":
    load_nse_security_master()