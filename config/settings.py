import os

ADMIN_ID = os.getenv("ADMIN_ID", "8223004316")

# Super admins — comma-separated in env var, or hardcoded fallback
# All IDs in this set get full admin access
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
