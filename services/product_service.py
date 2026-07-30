from database.repositories.category_repository import CategoryRepository
from database.repositories.product_repository import ProductRepository

class ProductService:
    def __init__(self, session):
        self.category_repo = CategoryRepository(session)
        self.product_repo = ProductRepository(session)

    async def get_categories(self):
        return await self.category_repo.get_active_categories()

    async def get_products(self, category_ids):
        if not category_ids:
            return []
        category_id = category_ids[0]
        return await self.product_repo.get_products_by_category(category_id)