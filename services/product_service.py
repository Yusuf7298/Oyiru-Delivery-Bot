from database.repositories.category_repository import CategoryRepository
from database.repositories.product_repository import ProductRepository

class ProductService:
    def __init__(self, session):
        self.category_repo = CategoryRepository(session)
        self.product_repo = ProductRepository(session)
    async def get_categories(self):
        return await self.category_repo.get_all()
    async def get_products(self, category_ids):
        return await self.product_repo.get_products_by_categories(category_ids)