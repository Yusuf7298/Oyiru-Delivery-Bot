from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(
        String(30),
        default="customer",
    )
    hotel_id: Mapped[int | None] = mapped_column(
        ForeignKey("hotels.id"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    hotel = relationship(
        "Hotel",
        back_populates="users",
    )
    orders = relationship(
        "Order",
        back_populates="customer",
        cascade="all, delete-orphan",)