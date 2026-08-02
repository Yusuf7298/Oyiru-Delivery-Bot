from __future__ import annotations
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Column,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from database.base import Base
class OrderStatus(str, Enum):
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    PREPARING = "Preparing"
    PACKED = "Packed"
    OUT_FOR_DELIVERY = "Out For Delivery"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    order_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    hotel_id: Mapped[int] = mapped_column(
        ForeignKey("hotels.id"),
        nullable=False,
        index=True,
    )
    delivery_partner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,)
    driver_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    status: Mapped[OrderStatus] = mapped_column(
        SqlEnum(OrderStatus),
        default=OrderStatus.SUBMITTED,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    telegram_file_id: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )
    file_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    original_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rating: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    feedback: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    returns: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        )
    customer = relationship(
        "User",
        foreign_keys=[customer_id],
        back_populates="orders")
    hotel = relationship(
        "Hotel",
        back_populates="orders")
    delivery_partner = relationship(
        "User",
        foreign_keys=[delivery_partner_id],
        back_populates="deliveries",)
    
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    returned_items = relationship(
        "ReturnedItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )