from sqlalchemy import select
from database.models.category import Category
from database.repositories.base_repository import BaseRepository
class CategoryRepository(BaseRepository):
    def __init__(self, session):
        self.session = session
    async def get_all(self): # type: ignore
        result = await self.session.execute(
            select(Category).where(
                Category.is_active == True
            )
        )
        return result.scalars().all()