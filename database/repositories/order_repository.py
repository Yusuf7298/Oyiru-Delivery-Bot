from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem
from utils.helpers import generate_order_number
class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    async def create_order(self, customer_id: int, hotel_id: int, items: list, note: str | None = None,):
        order = Order(order_number="TEMP", customer_id=customer_id, hotel_id=hotel_id,status=OrderStatus.SUBMITTED, note=note,)
        self.session.add(order)
        await self.session.flush()
        order.order_number = generate_order_number(order.id)
        for item in items:
            order_item = OrderItem(order_id=order.id, product_id=item["product_id"],quantity=item["quantity"],)
            self.session.add(order_item)
        await self.session.commit()
        await self.session.refresh(order)
        return order