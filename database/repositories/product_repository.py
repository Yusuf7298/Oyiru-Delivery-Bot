from typing import List, Optional, Any
from database.models.product import Product
from database.models.category import Category
from database.repositories.base_repository import BaseRepository

class ProductRepository(BaseRepository):
    def __init__(self, session: Any):
        super().__init__(session)

    async def _populate_category(self, product: Product) -> Product:
        if product and product.category_id and not product.category:
            doc = await self.db["categories"].find_one({"_id": product.category_id})
            if doc:
                product.category = Category.from_dict(doc)
        return product

    async def get_all(self) -> List[Product]: # type: ignore
        cursor = self.db["products"].find({}).sort("name", 1)
        products = []
        async for doc in cursor:
            prod = Product.from_dict(doc)
            await self._populate_category(prod)
            products.append(prod)
        return products

    async def get_active_products(self) -> List[Product]:
        cursor = self.db["products"].find({"is_active": True}).sort("name", 1)
        products = []
        async for doc in cursor:
            prod = Product.from_dict(doc)
            await self._populate_category(prod)
            products.append(prod)
        return products

    async def get_products_by_category(self, category_id: int) -> List[Product]:
        cursor = self.db["products"].find({
            "category_id": category_id,
            "is_active": True
        }).sort("name", 1)
        products = []
        async for doc in cursor:
            prod = Product.from_dict(doc)
            await self._populate_category(prod)
            products.append(prod)
        return products

    async def get_all_by_category(self, category_id: int) -> List[Product]:
        cursor = self.db["products"].find({
            "category_id": category_id
        }).sort("name", 1)
        products = []
        async for doc in cursor:
            prod = Product.from_dict(doc)
            await self._populate_category(prod)
            products.append(prod)
        return products

    async def get_by_id(self, product_id: int) -> Optional[Product]:  # type: ignore
        doc = await self.db["products"].find_one({"_id": product_id})
        if not doc:
            return None
        prod = Product.from_dict(doc)
        await self._populate_category(prod)
        return prod

    async def get_by_name_in_category(self, name: str, category_id: int) -> Optional[Product]:
        doc = await self.db["products"].find_one({
            "name": name,
            "category_id": category_id
        })
        if not doc:
            return None
        prod = Product.from_dict(doc)
        await self._populate_category(prod)
        return prod

    async def create(self, product: Product) -> Product:
        return await self.add(product)

    async def update(self, product: Product) -> Product:
        await self.add(product)
        return product

    async def soft_delete(self, product: Product) -> Product:
        product.is_active = False
        await self.add(product)
        return product

    async def activate(self, product: Product) -> Product:
        product.is_active = True
        await self.add(product)
        return product
