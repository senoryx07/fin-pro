from sqlmodel import Field, SQLModel


class Security(SQLModel, table=True):
    __tablename__ = "securities"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    company_id: int = Field(
        foreign_key="companies.id",
        index=True,
    )

    ticker: str | None = Field(
        default=None,
        index=True,
    )

    isin: str | None = Field(
        default=None,
        index=True,
    )

    exchange: str = Field(
        index=True,
    )

    security_type: str = Field(
        default="EQUITY",
        index=True,
    )

    series: str | None = Field(
        default=None,
    )

    exchange_code: str | None = Field(
        default=None,
        index=True,
    )

    status: str = Field(
        default="ACTIVE",
        index=True,
    )