from sqlalchemy import select
from database.models.product import Product
from database.repositories.base_repository import BaseRepository
class ProductRepository(BaseRepository):
    async def get_by_category(self, category_id: int):
        result = await self.session.execute(
            select(Product).where(
                Product.category_id == category_id,
                Product.is_active == True,
            )
        )
        return result.scalars().all()
    async def get_products(self, category_ids: list[int]):
        result = await self.session.execute(
            select(Product).where(
                Product.category_id.in_(category_ids),
                Product.is_active == True,
            )
        )
        return result.scalars().all()