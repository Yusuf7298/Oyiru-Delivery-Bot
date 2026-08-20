from typing import Optional, Any, Dict
from database.base import Base

class OrderItem(Base):
    def __init__(
        self,
        id: Optional[int] = None,
        order_id: int = 0,
        product_id: int = 0,
        quantity: float = 0.0,
        order: Optional[Any] = None,
        product: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.id = id
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.order = order
        self.product = product

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderItem":
        if not data:
            return None # type: ignore
        d = dict(data)
        d["id"] = d.get("id") or d.get("_id")
        return cls(**d)