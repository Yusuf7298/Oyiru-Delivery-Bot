from typing import List, Optional, Any
from database.models.hotel import Hotel
from database.repositories.base_repository import BaseRepository

class HotelRepository(BaseRepository):
    def __init__(self, session: Any):
        super().__init__(session)

    async def get_all(self) -> List[Hotel]: # type: ignore
        cursor = self.db["hotels"].find({}).sort("name", 1)
        hotels = []
        async for doc in cursor:
            hotels.append(Hotel.from_dict(doc))
        return hotels

    async def get_active_hotels(self) -> List[Hotel]:
        cursor = self.db["hotels"].find({"is_active": True}).sort("name", 1)
        hotels = []
        async for doc in cursor:
            hotels.append(Hotel.from_dict(doc))
        return hotels

    async def get_all_active(self) -> List[Hotel]:
        return await self.get_active_hotels()

    async def get_unclaimed_active_hotels(self, claimed_ids: list) -> List[Hotel]:
        query: dict = {"is_active": True}
        if claimed_ids:
            query["_id"] = {"$nin": claimed_ids}
        cursor = self.db["hotels"].find(query).sort("name", 1)
        hotels = []
        async for doc in cursor:
            hotels.append(Hotel.from_dict(doc))
        return hotels

    async def create(self, hotel: Hotel) -> Hotel:
        return await self.add(hotel)

    async def get_by_name(self, name: str) -> Optional[Hotel]:
        doc = await self.db["hotels"].find_one({"name": name})
        return Hotel.from_dict(doc) if doc else None

    async def get_by_id(self, hotel_id: int) -> Optional[Hotel]:  # type: ignore
        doc = await self.db["hotels"].find_one({"_id": hotel_id})
        return Hotel.from_dict(doc) if doc else None

    async def update(self, hotel: Hotel) -> Hotel:
        await self.add(hotel)
        return hotel

    async def soft_delete(self, hotel: Hotel) -> Hotel:
        hotel.is_active = False
        await self.add(hotel)
        return hotel

    async def activate(self, hotel: Hotel) -> Hotel:
        hotel.is_active = True
        await self.add(hotel)
        return hotel