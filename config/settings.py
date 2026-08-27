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

ORDERS_GROUP_ID          = os.getenv("ORDERS_GROUP_ID",          ADMIN_ID)
STORE_MANAGERS_GROUP_ID  = os.getenv("STORE_MANAGERS_GROUP_ID",  ADMIN_ID)
INVENTORY_GROUP_ID       = os.getenv("INVENTORY_GROUP_ID",       ADMIN_ID)
SALES_MANAGERS_GROUP_ID  = os.getenv("SALES_MANAGERS_GROUP_ID",  ADMIN_ID)
QUALITY_CONTROL_GROUP_ID = os.getenv("QUALITY_CONTROL_GROUP_ID", ADMIN_ID)
OPERATIONS_GROUP_ID      = os.getenv("OPERATIONS_GROUP_ID",      ADMIN_ID)
