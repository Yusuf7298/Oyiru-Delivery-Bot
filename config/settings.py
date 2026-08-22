import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8710717192:AAHNfwOej0IWmNqxxV7gYY67VMVKy7KnI_w")
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb+srv://ym47484988_db_user:sKZr5KRCuSPO9D0R@ethio-smart.i7vshtx.mongodb.net/?appName=Ethio-Smart")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "oyiru_delivery_bot")

ADMIN_ID = os.getenv("ADMIN_ID", "8223004316")

_extra = os.getenv("SUPER_ADMIN_IDS", "7269164159")
SUPER_ADMIN_IDS: set[str] = {
    str(ADMIN_ID).strip(),
    *[s.strip() for s in _extra.split(",") if s.strip()],
}

ORDERS_GROUP_ID          = os.getenv("ORDERS_GROUP_ID",          ADMIN_ID)
STORE_MANAGERS_GROUP_ID  = os.getenv("STORE_MANAGERS_GROUP_ID",  ADMIN_ID)
INVENTORY_GROUP_ID       = os.getenv("INVENTORY_GROUP_ID",       ADMIN_ID)
SALES_MANAGERS_GROUP_ID  = os.getenv("SALES_MANAGERS_GROUP_ID",  ADMIN_ID)
QUALITY_CONTROL_GROUP_ID = os.getenv("QUALITY_CONTROL_GROUP_ID", ADMIN_ID)
OPERATIONS_GROUP_ID      = os.getenv("OPERATIONS_GROUP_ID",      ADMIN_ID)
