from enum import Enum
class OrderStatus(str, Enum):
    SUBMITTED        = "Submitted"
    APPROVED         = "Approved"
    PREPARING        = "Preparing"
    PACKED           = "Packed"
    OUT_FOR_DELIVERY = "Out For Delivery"
    DELIVERED        = "Delivered"
    CANCELLED        = "Cancelled"
