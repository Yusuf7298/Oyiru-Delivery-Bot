from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
class ReturnedItem(Base):
    __tablename__ = "returned_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(
        String(1000), nullable=False
    )
    photo_file_id: Mapped[str | None] = mapped_column(
        String(250), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    order = relationship("Order", back_populates="returned_items")
