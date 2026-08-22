from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum
from database.base import Base

class UserRole(str, Enum):
    CUSTOMER = "customer"
    HOTEL = "hotel"
    DELIVERY = "delivery"
    ADMIN = "admin"

class User(Base):
    def __init__(
        self,
        id: Optional[int] = None,
        telegram_id: int = 0,
        full_name: str = "",
        username: Optional[str] = None,
        phone: Optional[str] = None,
        role: Any = UserRole.CUSTOMER,
        hotel_id: Optional[int] = None,
        language: str = "en",
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        hotel: Optional[Any] = None,
        orders: Optional[Any] = None,
        deliveries: Optional[Any] = None,
        delivery_profile: Optional[Any] = None,
        approved_delivery_partners: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.id = id
        self.telegram_id = telegram_id
        self.full_name = full_name
        self.username = username
        self.phone = phone
        if isinstance(role, str):
            try:
                self.role = UserRole(role)
            except ValueError:
                self.role = role
        else:
            self.role = role or UserRole.CUSTOMER
        self.hotel_id = hotel_id
        self.language = language or "en"
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.hotel = hotel
        self.orders = orders or []
        self.deliveries = deliveries or []
        self.delivery_profile = delivery_profile
        self.approved_delivery_partners = approved_delivery_partners or []

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if "role" in data and hasattr(data["role"], "value"):
            data["role"] = data["role"].value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        if not data:
            return None # type: ignore
        d = dict(data)
        d["id"] = d.get("id") or d.get("_id")
        return cls(**d)

