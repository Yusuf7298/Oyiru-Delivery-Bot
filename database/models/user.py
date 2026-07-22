from datetime import datetime
from enum import Enum
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class UserRole(str, Enum):
    CUSTOMER = "customer"
    HOTEL = "hotel"
    DELIVERY = "delivery"
    ADMIN = "admin"
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
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole),
        default=UserRole.CUSTOMER,
        nullable=False,
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
    deliveries = relationship(
        "Order",
        foreign_keys="Order.delivery_partner_id",
        back_populates="delivery_partner",
    )