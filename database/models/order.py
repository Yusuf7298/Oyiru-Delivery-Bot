from typing import Optional, Any, List, Dict
from datetime import datetime
from enum import Enum
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
    def __init__(
        self,
        id: Optional[int] = None,
        order_number: str = "",
        customer_id: int = 0,
        hotel_id: int = 0,
        delivery_partner_id: Optional[int] = None,
        driver_name: Optional[str] = None,
        accepted_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        delivered_at: Optional[datetime] = None,
        status: Any = OrderStatus.SUBMITTED,
        note: Optional[str] = None,
        file_path: Optional[str] = None,
        telegram_file_id: Optional[str] = None,
        file_type: Optional[str] = None,
        original_filename: Optional[str] = None,
        uploaded_at: Optional[datetime] = None,
        rating: Optional[int] = None,
        feedback: Optional[str] = None,
        returns: Optional[str] = None,
        created_at: Optional[datetime] = None,
        customer: Optional[Any] = None,
        hotel: Optional[Any] = None,
        delivery_partner: Optional[Any] = None,
        items: Optional[List[Any]] = None,
        returned_items: Optional[List[Any]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.id = id
        self.order_number = order_number
        self.customer_id = customer_id
        self.hotel_id = hotel_id
        self.delivery_partner_id = delivery_partner_id
        self.driver_name = driver_name
        self.accepted_at = accepted_at
        self.started_at = started_at
        self.delivered_at = delivered_at
        if isinstance(status, str):
            try:
                self.status = OrderStatus(status)
            except ValueError:
                self.status = status
        else:
            self.status = status or OrderStatus.SUBMITTED
        self.note = note
        self.file_path = file_path
        self.telegram_file_id = telegram_file_id
        self.file_type = file_type
        self.original_filename = original_filename
        self.uploaded_at = uploaded_at
        self.rating = rating
        self.feedback = feedback
        self.returns = returns
        self.created_at = created_at or datetime.utcnow()
        self.customer = customer
        self.hotel = hotel
        self.delivery_partner = delivery_partner
        self.items = items or []
        self.returned_items = returned_items or []

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if "status" in data and hasattr(data["status"], "value"):
            data["status"] = data["status"].value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        if not data:
            return None # type: ignore
        d = dict(data)
        d["id"] = d.get("id") or d.get("_id")
        return cls(**d)