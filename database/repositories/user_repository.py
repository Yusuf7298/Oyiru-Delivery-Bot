from typing import List, Optional, Any
from database.models.user import User, UserRole
from database.models.hotel import Hotel
from database.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self, session: Any):
        super().__init__(session)

    async def _populate_hotel(self, user: User) -> User:
        if user and user.hotel_id and not user.hotel:
            doc = await self.db["hotels"].find_one({"_id": user.hotel_id})
            if doc:
                user.hotel = Hotel.from_dict(doc)
        return user

    async def create_user(self, user: User) -> User:
        return await self.add(user)

    async def create(self, user: User) -> User:
        return await self.add(user)

    async def get_customers(self) -> List[User]:
        cursor = self.db["users"].find({"role": UserRole.CUSTOMER.value}).sort("full_name", 1)
        users = []
        async for doc in cursor:
            user = User.from_dict(doc)
            await self._populate_hotel(user)
            users.append(user)
        return users

    async def get_by_role(self, role: str) -> List[User]:
        role_norm = role.lower().strip()
        if role_norm in ("hotel_admin", "hotel"):
            roles_filter = ["hotel_admin", "hotel"]
        elif role_norm in ("driver", "delivery"):
            roles_filter = ["driver", "delivery"]
        else:
            roles_filter = [role_norm]

        cursor = self.db["users"].find({"role": {"$in": roles_filter}}).sort("full_name", 1)
        users = []
        async for doc in cursor:
            users.append(User.from_dict(doc))
        return users

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        doc = await self.db["users"].find_one({"telegram_id": telegram_id})
        if not doc:
            return None
        user = User.from_dict(doc)
        await self._populate_hotel(user)
        return user

    async def get_by_username(self, username: str) -> Optional[User]:
        if not username:
            return None
        import re
        clean = username.lstrip("@").strip()
        doc = await self.db["users"].find_one({
            "username": {"$regex": f"^{re.escape(clean)}$", "$options": "i"}
        })
        if not doc:
            return None
        user = User.from_dict(doc)
        await self._populate_hotel(user)
        return user

    async def get_by_phone(self, phone: str) -> Optional[User]:
        if not phone:
            return None
        from utils.helpers import normalize_ethiopian_phone
        norm = normalize_ethiopian_phone(phone)
        variations = [phone.strip()]
        if norm:
            variations.append(norm)
            variations.append("0" + norm[4:])
            variations.append(norm[1:])
            variations.append(norm[4:])

        doc = await self.db["users"].find_one({"phone": {"$in": variations}})
        if not doc:
            return None
        user = User.from_dict(doc)
        await self._populate_hotel(user)
        return user

    async def get_delivery_partners(self) -> List[User]:
        cursor = self.db["users"].find({
            "role": {"$in": ["driver", "delivery"]},
            "is_active": True
        }).sort("full_name", 1)
        users = []
        async for doc in cursor:
            users.append(User.from_dict(doc))
        return users

    async def get(self, user_id: int) -> Optional[User]:
        doc = await self.db["users"].find_one({"_id": user_id})
        if not doc:
            return None
        user = User.from_dict(doc)
        await self._populate_hotel(user)
        return user

    async def get_all_users(self) -> List[User]:
        cursor = self.db["users"].find({}).sort([("role", 1), ("full_name", 1)])
        users = []
        async for doc in cursor:
            users.append(User.from_dict(doc))
        return users

    async def set_role(self, user: User, role: str) -> User:
        user.role = role
        user.is_active = True
        await self.add(user)
        return user

    async def set_active(self, user: User, active: bool) -> User:
        user.is_active = active
        await self.add(user)
        return user

    async def get_active_by_roles(self, roles: list) -> List[User]:
        expanded = []
        for r in roles:
            r_norm = r.lower().strip()
            if r_norm in ("hotel", "hotel_admin"):
                expanded.extend(["hotel", "hotel_admin"])
            elif r_norm in ("delivery", "driver"):
                expanded.extend(["delivery", "driver"])
            else:
                expanded.append(r_norm)
        cursor = self.db["users"].find({
            "role": {"$in": list(set(expanded))},
            "is_active": True
        }).sort([("role", 1), ("full_name", 1)])
        users = []
        async for doc in cursor:
            users.append(User.from_dict(doc))
        return users

    async def get_claimed_hotel_ids(self) -> List[int]:
        cursor = self.db["users"].find({
            "role": {"$in": ["hotel", "hotel_admin"]},
            "hotel_id": {"$ne": None}
        })
        claimed_ids = []
        async for doc in cursor:
            hid = doc.get("hotel_id")
            if hid is not None and hid not in claimed_ids:
                claimed_ids.append(hid)
        return claimed_ids

    async def get_hotel_admin(self, hotel_id: int) -> Optional[User]:
        doc = await self.db["users"].find_one({
            "role": {"$in": ["hotel", "hotel_admin"]},
            "hotel_id": hotel_id
        })
        if not doc:
            return None
        user = User.from_dict(doc)
        await self._populate_hotel(user)
        return user

    async def get_hotel_staff(self, hotel_id: int) -> List[User]:
        cursor = self.db["users"].find({
            "role": UserRole.CUSTOMER.value,
            "hotel_id": hotel_id
        }).sort("full_name", 1)
        staff = []
        async for doc in cursor:
            user = User.from_dict(doc)
            await self._populate_hotel(user)
            staff.append(user)
        return staff

    async def update_username(self, telegram_id: int, username: Optional[str]) -> None:
        if username:
            await self.db["users"].update_one(
                {"telegram_id": telegram_id},
                {"$set": {"username": username}}
            )

