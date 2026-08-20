from typing import Optional, Any, Dict
from datetime import datetime
from database.base import Base

class Hotel(Base):
    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        address: Optional[str] = None,
        phone: Optional[str] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        users: Optional[Any] = None,
        orders: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.id = id
        self.name = name
        self.address = address
        self.phone = phone
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.users = users or []
        self.orders = orders or []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hotel":
        if not data:
            return None # type: ignore
        d = dict(data)
        d["id"] = d.get("id") or d.get("_id")
        return cls(**d)