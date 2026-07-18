import asyncio
from database.session import AsyncSessionLocal
from database.models.category import Category
categories = [
    "Fruits",
    "Vegetables",
    "Spices",
    "Dry Foods",
    "Grains",
    "Hotel Supplies"
]
async def main():
    async with AsyncSessionLocal() as session:
        for name in categories:
            session.add(Category(name=name))
        await session.commit()
        print("✅ Categories Seeded")
if __name__ == "__main__":
    asyncio.run(main())