from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem
from database.repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository):
    async def create_order(self, order: Order) -> Order:
        return await self.add(order)
    async def get_order(self, order_id: int):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.delivery_partner),
            )
            .where(Order.id == order_id) # type: ignore
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, order_number: str):
        result = await self.session.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def pending_orders(self):
        """All Submitted orders — Store Manager review queue."""
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(Order.status == OrderStatus.SUBMITTED)
            .order_by(Order.created_at)
        )
        return result.scalars().all()

    async def get_approved_no_driver(self):
        """Approved orders with no delivery partner assigned yet."""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.customer), selectinload(Order.hotel))
            .where(
                Order.status == OrderStatus.APPROVED,
                Order.delivery_partner_id.is_(None),
            )
            .order_by(Order.created_at)
        )
        return result.scalars().all()

    async def get_active_orders_all(self):
        """All in-progress orders — for Store Manager active view."""
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(
                Order.status.in_([
                    OrderStatus.APPROVED,
                    OrderStatus.PREPARING,
                    OrderStatus.PACKED,
                    OrderStatus.OUT_FOR_DELIVERY,
                ])
            )
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_new_orders(self, hotel_id: int):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(Order.hotel_id == hotel_id, Order.status == OrderStatus.SUBMITTED)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_active_orders(self, hotel_id: int):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(
                Order.hotel_id == hotel_id,
                Order.status.in_([
                    OrderStatus.APPROVED,
                    OrderStatus.PREPARING,
                    OrderStatus.PACKED,
                    OrderStatus.OUT_FOR_DELIVERY,
                ])
            )
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_order_history(self, hotel_id: int):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(
                Order.hotel_id == hotel_id,
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.CANCELLED])
            )
            .order_by(Order.created_at.desc())
            .limit(50)
        )
        return result.scalars().all()

    async def get_last_order(self, customer_id: int):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_customer_orders(self, customer_id: int):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_hotel_by_telegram(self, telegram_id: int):
        from database.models.user import User
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.hotel))
            .where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_driver_orders(self, driver_id: int):
        async def _fetch(statuses):
            r = await self.session.execute(
                select(Order)
                .options(selectinload(Order.customer), selectinload(Order.hotel))
                .where(
                    Order.delivery_partner_id == driver_id,
                    Order.status.in_(statuses),
                )
                .order_by(Order.created_at.desc())
            )
            return r.scalars().all()

        return {
            "assigned":  await _fetch([OrderStatus.APPROVED]),
            "accepted":  await _fetch([OrderStatus.OUT_FOR_DELIVERY]),
            "completed": await _fetch([OrderStatus.DELIVERED]),
        }

    async def approve_order(self, order_id: int, driver_name: str):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(Order.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            return None, "not_found"
        if order.status != OrderStatus.SUBMITTED:
            return order, "already_processed"
        order.status = OrderStatus.APPROVED
        order.driver_name = driver_name.strip()
        await self.session.commit()
        return await self.get_order(order_id), "ok"

    async def reject_order(self, order_id: int, reason: str):
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            return None, "not_found"
        if order.status != OrderStatus.SUBMITTED:
            return order, "already_processed"
        order.status = OrderStatus.CANCELLED
        existing = order.note or ""
        order.note = (
            f"[REJECTED: {reason.strip()}]"
            + (f" — {existing}" if existing else "")
        )
        await self.session.commit()
        return await self.get_order(order_id), "ok"

    async def assign_driver(self, order_id: int, driver_id: int):
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(Order.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            return None, "not_found"
        if order.status not in (OrderStatus.SUBMITTED, OrderStatus.APPROVED):
            return order, "not_approved"
        if order.delivery_partner_id is not None:
            return order, "already_assigned"
        order.delivery_partner_id = driver_id
        if order.status == OrderStatus.SUBMITTED:
            order.status = OrderStatus.APPROVED
        await self.session.commit()
        return await self.get_order(order_id), "ok"

    async def update_order_status(self, order_id: int, status: OrderStatus):
        order = await self.get_order(order_id)
        if order:
            order.status = status
            if status == OrderStatus.DELIVERED:
                order.delivered_at = datetime.now(timezone.utc)
            await self.session.commit()
            return await self.get_order(order_id)
        return order

    async def pending_assignment_orders(self):
        return await self.pending_orders()

    async def assign_internal_driver(self, order_id: int, driver_name: str):
        order, _ = await self.approve_order(order_id, driver_name)
        return order

    async def accept_order(self, order_id: int):
        return await self.update_order_status(order_id, OrderStatus.OUT_FOR_DELIVERY)

    async def driver_accept(self, order_id: int, driver_id: int):
        """Driver accepts an assigned order → OUT_FOR_DELIVERY."""
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(Order.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            return None, "not_found"
        if order.delivery_partner_id != driver_id:
            return order, "not_assigned"
        # Allow accept from APPROVED, PREPARING, or PACKED — SM may have advanced status
        if order.status not in (OrderStatus.APPROVED, OrderStatus.PREPARING, OrderStatus.PACKED):
            return order, "wrong_status"
        order.status = OrderStatus.OUT_FOR_DELIVERY
        order.accepted_at = datetime.now(timezone.utc)
        await self.session.commit()
        return await self.get_order(order_id), "ok"

    async def driver_complete(self, order_id: int, driver_id: int):
        """Driver marks delivery as completed → DELIVERED."""
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(Order.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            return None, "not_found"
        if order.delivery_partner_id != driver_id:
            return order, "not_assigned"
        if order.status != OrderStatus.OUT_FOR_DELIVERY:
            return order, "wrong_status"
        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.now(timezone.utc)
        await self.session.commit()
        return await self.get_order(order_id), "ok"
