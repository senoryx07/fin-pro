from sqlmodel import Session, select

from backend.app.database.database import engine
from backend.app.models.company import Company
from backend.app.models.security import Security


COMPANIES = [
    Company(
        name="Reliance Industries Limited",
        sector="Energy",
        industry="Integrated Oil & Gas",
        description=(
            "Reliance Industries Limited is a diversified Indian company "
            "with operations across energy, petrochemicals, retail and "
            "digital services."
        ),
    ),
    Company(
        name="Tata Consultancy Services Limited",
        sector="Information Technology",
        industry="IT Services",
        description=(
            "Tata Consultancy Services is a global information technology "
            "services, consulting and business solutions company."
        ),
    ),
    Company(
        name="Infosys Limited",
        sector="Information Technology",
        industry="IT Services",
        description=(
            "Infosys is a global provider of digital services, consulting "
            "and technology solutions."
        ),
    ),
    Company(
        name="HDFC Bank Limited",
        sector="Financial Services",
        industry="Banks",
        description=(
            "HDFC Bank is an Indian banking and financial services company "
            "providing a range of banking products and services."
        ),
    ),
    Company(
        name="Asian Paints Limited",
        sector="Consumer Goods",
        industry="Paints & Coatings",
        description=(
            "Asian Paints is an Indian company operating primarily in "
            "paints, coatings and related home-improvement products."
        ),
    ),
]


SECURITY_SEED = [
    {
        "company_name": "Reliance Industries Limited",
        "ticker": "RELIANCE",
        "exchange": "NSE",
        "series": "EQ",
    },
    {
        "company_name": "Tata Consultancy Services Limited",
        "ticker": "TCS",
        "exchange": "NSE",
        "series": "EQ",
    },
    {
        "company_name": "Infosys Limited",
        "ticker": "INFY",
        "exchange": "NSE",
        "series": "EQ",
    },
    {
        "company_name": "HDFC Bank Limited",
        "ticker": "HDFCBANK",
        "exchange": "NSE",
        "series": "EQ",
    },
    {
        "company_name": "Asian Paints Limited",
        "ticker": "ASIANPAINT",
        "exchange": "NSE",
        "series": "EQ",
    },
]


def seed_companies() -> None:
    with Session(engine) as session:
        existing_companies = session.exec(
            select(Company)
        ).all()

        if existing_companies:
            print(
                "Companies already exist. "
                "Skipping company seed."
            )
            return

        session.add_all(COMPANIES)
        session.commit()

        print(
            f"Seeded {len(COMPANIES)} companies "
            "into the database."
        )

        seed_securities(session)


def seed_securities(
    session: Session,
) -> None:
    existing_securities = session.exec(
        select(Security)
    ).all()

    if existing_securities:
        print(
            "Securities already exist. "
            "Skipping security seed."
        )
        return

    companies = session.exec(
        select(Company)
    ).all()

    company_map = {
        company.name: company
        for company in companies
    }

    securities = []

    for security_data in SECURITY_SEED:
        company = company_map.get(
            security_data["company_name"]
        )

        if company is None:
            continue

        securities.append(
            Security(
                company_id=company.id,
                ticker=security_data["ticker"],
                isin=None,
                exchange=security_data["exchange"],
                security_type="EQUITY",
                series=security_data["series"],
                exchange_code=None,
                status="ACTIVE",
            )
        )

    session.add_all(securities)
    session.commit()

    print(
        f"Seeded {len(securities)} securities "
        "into the database."
    )