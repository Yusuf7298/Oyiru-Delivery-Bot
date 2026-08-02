from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from database.base import Base
class Hotel(Base):
    __tablename__ = "hotels"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )
    address: Mapped[str | None] = mapped_column(
        String(250),
    )
    phone: Mapped[str | None] = mapped_column(
        String(30),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    users = relationship(
        "User",
        back_populates="hotel",
    )
    orders = relationship(
        "Order",
        back_populates="hotel"
    )