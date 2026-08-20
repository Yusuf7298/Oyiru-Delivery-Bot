from typing import Optional, Any, Dict
from datetime import datetime
from database.base import Base

class ReturnedItem(Base):
    def __init__(
        self,
        id: Optional[int] = None,
        order_id: int = 0,
        description: str = "",
        photo_file_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        order: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.id = id
        self.order_id = order_id
        self.description = description
        self.photo_file_id = photo_file_id
        self.created_at = created_at or datetime.utcnow()
        self.order = order

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReturnedItem":
        if not data:
            return None # type: ignore
        d = dict(data)
        d["id"] = d.get("id") or d.get("_id")
        return cls(**d)
