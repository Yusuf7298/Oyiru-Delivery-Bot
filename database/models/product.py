from typing import Optional, Any, Dict
from datetime import datetime
from database.base import Base

class Product(Base):
    def __init__(
        self,
        id: Optional[int] = None,
        category_id: int = 0,
        name: str = "",
        unit: str = "KG",
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        category: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.id = id
        self.category_id = category_id
        self.name = name
        self.unit = unit
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.category = category

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        if not data:
            return None # type: ignore
        d = dict(data)
        d["id"] = d.get("id") or d.get("_id")
        return cls(**d)