from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class CorporateInfo(SQLModel, table=True):
    """
    Latest announcements, corporate actions, board meetings and
    shareholding for one security, as fetched from NSE.
    """

    __tablename__ = "corporate_info"

    security_id: int = Field(
        foreign_key="securities.id",
        primary_key=True,
    )

    fetched_at: datetime

    data: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
