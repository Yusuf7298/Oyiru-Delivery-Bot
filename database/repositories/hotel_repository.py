from sqlalchemy import select
from database.models.hotel import Hotel
from database.repositories.base_repository import BaseRepository
class HotelRepository(BaseRepository):
    async def get_active_hotels(self):
        result = await self.session.execute(
            select(Hotel).where(
                Hotel.is_active == True
            )
        )
        return result.scalars().all()
    async def create(self, hotel: Hotel):
        return await self.add(hotel)
    async def get_by_name(self, name: str):
        result = await self.session.execute(
        select(Hotel).where(
            Hotel.name == name
        )
    )
        return result.scalar_one_or_none()