from enum import Enum
class UserRole(str, Enum):
    CUSTOMER      = "customer"
    HOTEL         = "hotel"       # Store Manager
    DELIVERY      = "delivery"    # Delivery Partner
    ADMIN         = "admin"
