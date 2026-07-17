from enum import Enum
class UserRole(str, Enum):
    CUSTOMER = "customer"
    INVENTORY = "inventory"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class Language(str, Enum):
    EN = "en"
    OM = "om"
    AM = "am"

class OrderStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    INVENTORY_CHECKING = "inventory_checking"
    PREPARING = "preparing"
    PACKED = "packed"
    READY_FOR_DELIVERY = "ready_for_delivery"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderType(str, Enum):
    LIST = "list"
    IMAGE = "image"