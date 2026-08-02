from __future__ import annotations
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
    role: Mapped[str] = mapped_column(
        String(30),
        default=UserRole.CUSTOMER.value,
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
        foreign_keys="Order.customer_id",
        back_populates="customer",
        cascade="all, delete-orphan",)
    deliveries = relationship(
        "Order",
        foreign_keys="Order.delivery_partner_id",
        back_populates="delivery_partner",
    )
    delivery_profile = relationship(
        "DeliveryPartner",
        foreign_keys="DeliveryPartner.user_id",
        back_populates="user",
        uselist=False,
    )

    approved_delivery_partners = relationship(
        "DeliveryPartner",
        foreign_keys="DeliveryPartner.approved_by",
        back_populates="approver",
    )