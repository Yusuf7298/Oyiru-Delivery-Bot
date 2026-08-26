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

    async def get_customers(self) -> List[User]:
        cursor = self.db["users"].find({"role": UserRole.CUSTOMER.value}).sort("full_name", 1)
        users = []
        async for doc in cursor:
            user = User.from_dict(doc)
            await self._populate_hotel(user)
            users.append(user)
        return users

    async def get_by_role(self, role: str) -> List[User]:
        cursor = self.db["users"].find({"role": role}).sort("full_name", 1)
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

    async def get_delivery_partners(self) -> List[User]:
        cursor = self.db["users"].find({
            "role": UserRole.DELIVERY.value,
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
        cursor = self.db["users"].find({
            "role": {"$in": roles},
            "is_active": True
        }).sort([("role", 1), ("full_name", 1)])
        users = []
        async for doc in cursor:
            users.append(User.from_dict(doc))
        return users

    async def get_claimed_hotel_ids(self) -> List[int]:
        cursor = self.db["users"].find({
            "role": UserRole.HOTEL.value,
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
            "role": UserRole.HOTEL.value,
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

