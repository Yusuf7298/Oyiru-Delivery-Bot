import asyncio
from database.session import AsyncSessionLocal
from database.models.hotel import Hotel
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
        for name in HOTELS:
            session.add(Hotel(name=name,is_active=True,))
        await session.commit()
        print("Hotels Seeded Successfully")
asyncio.run(main())