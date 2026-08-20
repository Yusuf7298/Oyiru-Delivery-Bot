from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum
from database.base import Base

class DeliveryPartnerStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    SUSPENDED = "Suspended"

class DeliveryPartner(Base):
    def __init__(
        self,
        id: Optional[int] = None,
        user_id: int = 0,
        vehicle_type: str = "",
        license_number: str = "",
        national_id: str = "",
        area: str = "",
        status: Any = DeliveryPartnerStatus.PENDING,
        approved_by: Optional[int] = None,
        approved_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        user: Optional[Any] = None,
        approver: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.id = id
        self.user_id = user_id
        self.vehicle_type = vehicle_type
        self.license_number = license_number
        self.national_id = national_id
        self.area = area
        if isinstance(status, str):
            try:
                self.status = DeliveryPartnerStatus(status)
            except ValueError:
                self.status = status
        else:
            self.status = status or DeliveryPartnerStatus.PENDING
        self.approved_by = approved_by
        self.approved_at = approved_at
        self.created_at = created_at or datetime.utcnow()
        self.user = user
        self.approver = approver

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if "status" in data and hasattr(data["status"], "value"):
            data["status"] = data["status"].value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeliveryPartner":
        if not data:
            return None # type: ignore
        d = dict(data)
        d["id"] = d.get("id") or d.get("_id")
        return cls(**d)