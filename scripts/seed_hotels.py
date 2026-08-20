import asyncio
from database.session import AsyncSessionLocal
from database.models.hotel import Hotel
from database.repositories.hotel_repository import HotelRepository

HOTELS = [
    "Skylight Hotel",
    "Hilton Addis",
    "Harmony Hotel",
    "Capital Hotel",
    "Inter Luxury",
    "Best Western",
]

async def main():
    async with AsyncSessionLocal() as session:
        repo = HotelRepository(session)
        for name in HOTELS:
            existing = await repo.get_by_name(name)
            if not existing:
                await repo.create(Hotel(name=name, is_active=True))
        print("Hotels Seeded Successfully")

if __name__ == "__main__":
    asyncio.run(main())