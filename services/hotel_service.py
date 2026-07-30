from database.repositories.hotel_repository import HotelRepository
class HotelService:
    def __init__(self, session):
        self.repo = HotelRepository(session)
    async def get_hotels(self):
        return await self.repo.get_active_hotels()
    async def get_hotel(self, hotel_id):
        return await self.repo.get_by_id(hotel_id)