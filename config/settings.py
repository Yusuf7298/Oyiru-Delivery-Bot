import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8710717192:AAHNfwOej0IWmNqxxV7gYY67VMVKy7KnI_w")
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb+srv://ym47484988_db_user:sKZr5KRCuSPO9D0R@ethio-smart.i7vshtx.mongodb.net/?appName=Ethio-Smart")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "oyiru_delivery_bot")

_admin_raw = os.getenv("ADMIN_ID", "8223004316")
_extra = os.getenv("SUPER_ADMIN_IDS", "7269164159")

SUPER_ADMIN_IDS: set[str] = set()
for raw in [_admin_raw, _extra]:
    for part in raw.split(","):
        part = part.strip()
        if part:
            SUPER_ADMIN_IDS.add(part)

ADMIN_ID = next(iter(SUPER_ADMIN_IDS)) if SUPER_ADMIN_IDS else "8223004316"

# 5 Dedicated Oyiru Channels:
# 1. OyruStore: Receives new customer order submissions
OYIRU_STORE_GROUP_ID                 = os.getenv("OYIRU_STORE_GROUP_ID", os.getenv("STORE_MANAGERS_GROUP_ID", ADMIN_ID))
# 2. OyruPurchase: Receives new customer order submissions and returned product reports
OYIRU_PURCHASE_GROUP_ID              = os.getenv("OYIRU_PURCHASE_GROUP_ID", os.getenv("INVENTORY_GROUP_ID", os.getenv("ORDERS_GROUP_ID", ADMIN_ID)))
# 3. OyruDelivery Confirmation: Receives delivery confirmation & proof of delivery from drivers
OYIRU_DELIVERY_CONFIRMATION_GROUP_ID = os.getenv("OYIRU_DELIVERY_CONFIRMATION_GROUP_ID", os.getenv("OPERATIONS_GROUP_ID", ADMIN_ID))
# 4. OyruFinance: Receives delivery confirmation & proof of delivery for finance processing
OYIRU_FINANCE_GROUP_ID               = os.getenv("OYIRU_FINANCE_GROUP_ID", os.getenv("SALES_MANAGERS_GROUP_ID", ADMIN_ID))
# 5. OyruFeedback Management: Receives customer feedback and rating reports
OYIRU_FEEDBACK_MANAGEMENT_GROUP_ID   = os.getenv("OYIRU_FEEDBACK_MANAGEMENT_GROUP_ID", os.getenv("QUALITY_CONTROL_GROUP_ID", ADMIN_ID))

# Legacy aliases for backward compatibility:
ORDERS_GROUP_ID          = OYIRU_PURCHASE_GROUP_ID
STORE_MANAGERS_GROUP_ID  = OYIRU_STORE_GROUP_ID
INVENTORY_GROUP_ID       = OYIRU_PURCHASE_GROUP_ID
SALES_MANAGERS_GROUP_ID  = OYIRU_FINANCE_GROUP_ID
QUALITY_CONTROL_GROUP_ID = OYIRU_FEEDBACK_MANAGEMENT_GROUP_ID
OPERATIONS_GROUP_ID      = OYIRU_DELIVERY_CONFIRMATION_GROUP_ID
