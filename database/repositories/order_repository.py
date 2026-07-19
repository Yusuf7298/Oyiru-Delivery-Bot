from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem
from utils.helpers import generate_order_number
from database.models.user import User
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
    

    async def get_new_orders(self, hotel_id):
        result = await self.session.execute(
            select(Order)
                .options(
                    selectinload(Order.customer),
                    selectinload(Order.items).selectinload(OrderItem.product), # type: ignore
                                                        )
                .where(
                    Order.hotel_id == hotel_id,
                    Order.status == OrderStatus.SUBMITTED,
                    )
                .order_by(Order.created_at.desc())
                )

        return result.scalars().all()
    
    async def get_hotel_by_telegram(self, telegram_id):
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()
    
    async def get_order(self, order_id):
        result = await self.session.execute(
            select(Order)
                .options(
                    selectinload(Order.customer),
                    selectinload(Order.items).selectinload(OrderItem.product),)
                .where(Order.id == order_id))
        return result.scalar_one_or_none()
    
    async def update_status(self, order_id, status):
        order = await self.get_order(order_id)
        if not order:
            return None
        order.status = status
        await self.session.commit()
        await self.session.refresh(order)
        return order