from sqlalchemy import select
from database.models.product import Product
from database.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository):

    async def get_all(self): # type: ignore
        result = await self.session.execute(
            select(Product).order_by(Product.name)
        )
        return result.scalars().all()

    async def get_products_by_category(self, category_id: int):
        result = await self.session.execute(
            select(Product)
            .where(
                Product.category_id == category_id,
                Product.is_active == True,
            )
            .order_by(Product.name)
        )
        return result.scalars().all()

    async def get_all_by_category(self, category_id: int):
        result = await self.session.execute(
            select(Product)
            .where(Product.category_id == category_id)
            .order_by(Product.name)
        )
        return result.scalars().all()

    async def get_by_id(self, product_id: int):  # type: ignore
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name_in_category(self, name: str, category_id: int):
        result = await self.session.execute(
            select(Product).where(
                Product.name == name,
                Product.category_id == category_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, product: Product):
        return await self.add(product)

    async def update(self, product: Product):
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def soft_delete(self, product: Product):
        product.is_active = False
        await self.session.commit()
        return product

    async def activate(self, product: Product):
        product.is_active = True
        await self.session.commit()
        return product
