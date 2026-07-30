from sqlalchemy import select
from database.models.category import Category
from database.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository):

    async def get_all(self): # type: ignore
        result = await self.session.execute(
            select(Category).order_by(Category.name)
        )
        return result.scalars().all()

    async def get_active_categories(self):
        result = await self.session.execute(
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.name)
        )
        return result.scalars().all()

    async def get_by_id(self, category_id: int):  # type: ignore
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str):
        result = await self.session.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, category: Category):
        return await self.add(category)

    async def update(self, category: Category):
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def soft_delete(self, category: Category):
        category.is_active = False
        await self.session.commit()
        return category

    async def activate(self, category: Category):
        category.is_active = True
        await self.session.commit()
        return category