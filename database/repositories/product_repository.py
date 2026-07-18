from sqlalchemy import select
from database.models.product import Product
from sqlalchemy.orm import selectinload
from database.repositories.base_repository import BaseRepository
class ProductRepository(BaseRepository):
    def __init__(self, session):
        self.session = session
    async def get_products_by_categories(self, category_ids):
        result = await self.session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.category_id.in_(category_ids),Product.is_active == True)
            .order_by(Product.category_id, Product.name))
        return result.scalars().all()
    
    async def get_products(self, category_ids: list[int]):
        result = await self.session.execute(
            select(Product).where(
                Product.category_id.in_(category_ids),
                Product.is_active == True,
            )
        )
        return result.scalars().all()