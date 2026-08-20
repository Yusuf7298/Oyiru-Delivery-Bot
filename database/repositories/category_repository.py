from typing import List, Optional, Any
from database.models.category import Category
from database.repositories.base_repository import BaseRepository

class CategoryRepository(BaseRepository):
    def __init__(self, session: Any):
        super().__init__(session)

    async def get_all(self) -> List[Category]: # type: ignore
        cursor = self.db["categories"].find({}).sort("name", 1)
        categories = []
        async for doc in cursor:
            categories.append(Category.from_dict(doc))
        return categories

    async def get_active_categories(self) -> List[Category]:
        cursor = self.db["categories"].find({"is_active": True}).sort("name", 1)
        categories = []
        async for doc in cursor:
            categories.append(Category.from_dict(doc))
        return categories

    async def get_by_id(self, category_id: int) -> Optional[Category]:  # type: ignore
        doc = await self.db["categories"].find_one({"_id": category_id})
        return Category.from_dict(doc) if doc else None

    async def get_by_name(self, name: str) -> Optional[Category]:
        doc = await self.db["categories"].find_one({"name": name})
        return Category.from_dict(doc) if doc else None

    async def create(self, category: Category) -> Category:
        return await self.add(category)

    async def update(self, category: Category) -> Category:
        await self.add(category)
        return category

    async def soft_delete(self, category: Category) -> Category:
        category.is_active = False
        await self.add(category)
        return category

    async def activate(self, category: Category) -> Category:
        category.is_active = True
        await self.add(category)
        return category