from sqlalchemy import select
from database.models.hotel import Hotel
from database.repositories.base_repository import BaseRepository

class HotelRepository(BaseRepository):
    async def get_all(self): # type: ignore
        result = await self.session.execute(
            select(Hotel).order_by(Hotel.name)
        )
        return result.scalars().all()

    async def get_active_hotels(self):
        result = await self.session.execute(
            select(Hotel).where(Hotel.is_active.is_(True)).order_by(Hotel.name)
        )
        return result.scalars().all()

    async def create(self, hotel: Hotel):
        return await self.add(hotel)

    async def get_by_name(self, name: str):
        result = await self.session.execute(
            select(Hotel).where(Hotel.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, hotel_id: int):  # type: ignore
        result = await self.session.execute(
            select(Hotel).where(Hotel.id == hotel_id)
        )
        return result.scalar_one_or_none()

    async def update(self, hotel: Hotel):
        await self.session.commit()
        await self.session.refresh(hotel)
        return hotel

    async def soft_delete(self, hotel: Hotel):
        hotel.is_active = False
        await self.session.commit()
        return hotel

    async def activate(self, hotel: Hotel):
        hotel.is_active = True
        await self.session.commit()
        return hotel