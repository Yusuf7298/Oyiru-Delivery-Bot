from __future__ import annotations
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from database.base import Base
class DeliveryPartnerStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    SUSPENDED = "Suspended"
class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    license_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    national_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    area: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    status: Mapped[DeliveryPartnerStatus] = mapped_column(
        SqlEnum(DeliveryPartnerStatus),
        default=DeliveryPartnerStatus.PENDING,
        nullable=False,
    )

    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="delivery_profile",
    )

    approver = relationship(
        "User",
        foreign_keys=[approved_by],
        back_populates="approved_delivery_partners",
    )