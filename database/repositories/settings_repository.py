import re
from typing import Dict, Any, Optional
from database.session import db

DEFAULT_SUPPORT = {
    "_id": "support_contact",
    "phone": "+251 98 438 6102",
    "email": "oyirusupport@gmail.com",
    "telegram_username": "Oyrudeliveryet",
    "telegram_link": "https://t.me/Oyrudeliveryet",
}

class SettingsRepository:
    def __init__(self, session: Any = None):
        self.db = session if session is not None else db

    async def get_support_contact(self) -> Dict[str, Any]:
        doc = await self.db["system_settings"].find_one({"_id": "support_contact"})
        if not doc:
            await self.db["system_settings"].update_one(
                {"_id": "support_contact"},
                {"$set": DEFAULT_SUPPORT},
                upsert=True
            )
            doc = DEFAULT_SUPPORT.copy()
        
        # Ensure telegram_link and phone_clean are always properly computed
        raw_tg = doc.get("telegram_username", "Oyrudeliveryet") or "Oyrudeliveryet"
        clean_tg = raw_tg.replace("https://t.me/", "").replace("http://t.me/", "").replace("t.me/", "").replace("@", "").strip()
        doc["telegram_username"] = clean_tg
        doc["telegram_link"] = f"https://t.me/{clean_tg}" if clean_tg else "https://t.me/Oyrudeliveryet"
        
        raw_phone = doc.get("phone", "+251 98 438 6102") or "+251 98 438 6102"
        doc["phone"] = raw_phone
        doc["phone_clean"] = re.sub(r"[^\d+]", "", raw_phone)
        return doc

    async def update_support_contact(
        self,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        telegram: Optional[str] = None
    ) -> Dict[str, Any]:
        update_data = {}
        if phone is not None:
            update_data["phone"] = phone.strip()
        if email is not None:
            update_data["email"] = email.strip()
        if telegram is not None:
            clean_tg = telegram.replace("https://t.me/", "").replace("http://t.me/", "").replace("t.me/", "").replace("@", "").strip()
            update_data["telegram_username"] = clean_tg
            update_data["telegram_link"] = f"https://t.me/{clean_tg}"

        if update_data:
            await self.db["system_settings"].update_one(
                {"_id": "support_contact"},
                {"$set": update_data},
                upsert=True
            )
        return await self.get_support_contact()

    async def reset_support_contact(self) -> Dict[str, Any]:
        await self.db["system_settings"].update_one(
            {"_id": "support_contact"},
            {"$set": DEFAULT_SUPPORT},
            upsert=True
        )
        return await self.get_support_contact()
