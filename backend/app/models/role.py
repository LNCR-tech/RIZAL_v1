from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, Text

from app.core.timezones import utc_now
from app.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True)
    code = Column(Text, unique=True, nullable=False, index=True)
    display_name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    @property
    def name(self) -> str:
        return self.code

    @name.setter
    def name(self, value: str) -> None:
        self.code = value
