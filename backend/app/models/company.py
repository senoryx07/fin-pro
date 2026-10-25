from sqlmodel import Field, SQLModel


class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    name: str

    sector: str = Field(
        index=True,
    )

    industry: str = Field(
        index=True,
    )

    description: str


class SecurityResponse(SQLModel):
    ticker: str | None
    exchange: str
    isin: str | None
    security_type: str
    series: str | None
    exchange_code: str | None
    status: str


class CompanyResponse(SQLModel):
    name: str
    sector: str
    industry: str
    description: str
    security: SecurityResponse