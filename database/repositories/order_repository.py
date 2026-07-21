from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem
from utils.helpers import generate_order_number
from database.models.user import User
from database.models.order import OrderStatus
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
            select(User)
            .options(selectinload(User.hotel))
            .where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()
    
    async def get_order(self, order_id):
        result = await self.session.execute(
            select(Order)
                .options(
                    selectinload(Order.customer),
                    selectinload(Order.items).selectinload(OrderItem.product),)
                .where(Order.id == order_id))
        return result.scalar_one_or_none()
    
    async def update_order_status(self, order_id: int, status: OrderStatus):
        order = await self.get_order(order_id)
        if not order:
            return None
        order.status = status
        await self.session.commit()
        await self.session.refresh(order)
        return order
    
    async def get_active_orders(self, hotel_id):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.items).selectinload(OrderItem.product),)
            .where(
            Order.hotel_id == hotel_id,
            Order.status.in_([
                OrderStatus.UNDER_REVIEW,
                OrderStatus.INVENTORY_CHECKING,
                OrderStatus.PREPARING,
                OrderStatus.PACKED,
                OrderStatus.READY_FOR_DELIVERY,
                OrderStatus.OUT_FOR_DELIVERY,
              ])
            )
           .order_by(Order.created_at.desc())
    )

        return result.scalars().all()
    
    async def get_order_history(self, hotel_id):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.items).selectinload(OrderItem.product),)
            .where(
            Order.hotel_id == hotel_id,
            Order.status.in_([
                OrderStatus.DELIVERED,
                OrderStatus.CANCELLED,
              ])
            )
           .order_by(Order.created_at.desc())
    )

        return result.scalars().all()
    
    async def get_available_deliveries(self):
        result = await self.session.execute(
            select(Order)
                .options(
                    selectinload(Order.customer),
                    selectinload(Order.hotel),
                    selectinload(Order.items).selectinload(OrderItem.product),)
                    .where(
                        Order.status == OrderStatus.READY_FOR_DELIVERY,
                        Order.delivery_partner_id == None,
                        )
                    .order_by(Order.created_at.asc()))

        return result.scalars().all()
    
    async def get_driver_orders(self, driver_id: int):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),)
            .where(
                Order.delivery_partner_id == driver_id,
                Order.status.in_([
                    OrderStatus.READY_FOR_DELIVERY,
                    OrderStatus.OUT_FOR_DELIVERY,]))
            .order_by(Order.created_at.desc()))
        return result.scalars().all()
    
    async def accept_delivery(self, order_id: int, driver_id: int):
        order = await self.get_order(order_id)
        if not order:
            return None

        order.delivery_partner_id = driver_id
        order.accepted_at = datetime.utcnow()
        order.status = OrderStatus.OUT_FOR_DELIVERY

        await self.session.commit()
        await self.session.refresh(order)
        return order
    
    async def complete_delivery(self, order_id: int):
        order = await self.get_order(order_id)
        if not order:
            return None
        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(order)
        return order
    
    async def get_driver_history(self, driver_id: int):
        result = await self.session.execute(
        select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),)
            .where(
                Order.delivery_partner_id == driver_id,
                Order.status == OrderStatus.DELIVERED,)
            .order_by(Order.delivered_at.desc()))
        return result.scalars().all()