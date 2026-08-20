import asyncio
from database.session import AsyncSessionLocal
from database.models.category import Category
from database.repositories.category_repository import CategoryRepository

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
        repo = CategoryRepository(session)
        for name in categories:
            existing = await repo.get_by_name(name)
            if not existing:
                await repo.create(Category(name=name))
        print("Categories Seeded Successfully")

if __name__ == "__main__":
    asyncio.run(main())