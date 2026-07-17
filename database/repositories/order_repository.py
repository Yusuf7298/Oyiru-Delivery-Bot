from sqlalchemy import select
from database.models.order import Order
from database.repositories.base_repository import BaseRepository
class OrderRepository(BaseRepository):
    async def create_order(self, order: Order):
        return await self.add(order)
    async def get_order(self, order_id: int):
        result = await self.session.execute(
            select(Order).where(
                Order.id == order_id
            )
        )
        return result.scalar_one_or_none()

    async def get_customer_orders(self, customer_id: int):
        result = await self.session.execute(
            select(Order).where(
                Order.customer_id == customer_id
            )
        )
        return result.scalars().all()

    async def update(self):
        await self.commit()