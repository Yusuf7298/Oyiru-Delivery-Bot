from typing import Dict, Any
from enum import Enum

RELATION_ATTRIBUTES = {
    "hotel", "customer", "delivery_partner", "driver", "user", 
    "orders", "deliveries", "approved_delivery_partners", "users",
    "category", "approver", "product", "order", "delivery_profile"
}

class Base:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _serialize_val(self, val: Any) -> Any:
        if val is None:
            return None
        if isinstance(val, Enum):
            return val.value
        if hasattr(val, "to_dict"):
            return val.to_dict()
        if isinstance(val, list):
            return [self._serialize_val(item) for item in val]
        if isinstance(val, dict):
            return {dk: self._serialize_val(dv) for dk, dv in val.items()}
        return val

    def to_dict(self) -> Dict[str, Any]:
        data = {}
        for k, v in self.__dict__.items():
            if k.startswith("_") and k != "_id":
                continue
            if k in RELATION_ATTRIBUTES:
                continue
            data[k] = self._serialize_val(v)
        return data

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_"))
        return f"<{self.__class__.__name__}({attrs})>"

