from sqlalchemy import select
from database.models.category import Category
from database.repositories.base_repository import BaseRepository
class CategoryRepository(BaseRepository):
    async def get_active_categories(self):
        result = await self.session.execute(
            select(Category).where(
                Category.is_active == True
            )
        )
        return result.scalars().all()