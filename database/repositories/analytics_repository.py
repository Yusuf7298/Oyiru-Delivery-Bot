from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, case, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem
from database.models.hotel import Hotel
from database.models.user import User
from database.models.product import Product

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def _start_of_week(dt: datetime) -> datetime:
    return _start_of_day(dt - timedelta(days=dt.weekday()))
def _start_of_month(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    async def _count_orders(self, since: datetime = None, # type: ignore
                            status: OrderStatus = None) -> int: # type: ignore
        q = select(func.count(Order.id))
        if since:
            q = q.where(Order.created_at >= since)
        if status:
            q = q.where(Order.status == status)
        result = await self.session.execute(q)
        return result.scalar() or 0

    async def orders_today(self) -> int:
        return await self._count_orders(since=_start_of_day(_now_utc()))

    async def orders_this_week(self) -> int:
        return await self._count_orders(since=_start_of_week(_now_utc()))

    async def orders_this_month(self) -> int:
        return await self._count_orders(since=_start_of_month(_now_utc()))

    async def orders_total(self) -> int:
        return await self._count_orders()
    async def count_by_status(self) -> dict:
        result = await self.session.execute(
            select(Order.status, func.count(Order.id))
            .group_by(Order.status)
        )
        return {row[0].value: row[1] for row in result.all()}

    async def avg_delivery_minutes(self) -> float | None:
        result = await self.session.execute(
            select(Order.accepted_at, Order.delivered_at)
            .where(
                Order.status == OrderStatus.DELIVERED,
                Order.accepted_at.isnot(None),
                Order.delivered_at.isnot(None),
            )
        )
        rows = result.all()
        if not rows:
            return None
        durations = [
            (r.delivered_at - r.accepted_at).total_seconds() / 60
            for r in rows
            if r.delivered_at and r.accepted_at
               and r.delivered_at > r.accepted_at
        ]
        return round(sum(durations) / len(durations), 1) if durations else None


    async def top_hotels(self, limit: int = 5) -> list[tuple[str, int]]:
        result = await self.session.execute(
            select(Hotel.name, func.count(Order.id).label("cnt"))
            .join(Order, Order.hotel_id == Hotel.id)
            .group_by(Hotel.id, Hotel.name)
            .order_by(text("cnt DESC"))
            .limit(limit)
        )
        return [(row.name, row.cnt) for row in result.all()]

    async def top_products(self, limit: int = 5) -> list[tuple[str, float, str]]:
        result = await self.session.execute(
            select(
                Product.name,
                func.sum(OrderItem.quantity).label("total_qty"),
                Product.unit,
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .group_by(Product.id, Product.name, Product.unit)
            .order_by(text("total_qty DESC"))
            .limit(limit)
        )
        return [(row.name, row.total_qty, row.unit) for row in result.all()]

    # ── Top Drivers by completed deliveries ───────────────────────────────────
    async def top_drivers(self, limit: int = 5) -> list[tuple[str, int]]:
        # driver_name field (internal string, no Telegram account required)
        result = await self.session.execute(
            select(Order.driver_name, func.count(Order.id).label("cnt"))
            .where(
                Order.status == OrderStatus.DELIVERED,
                Order.driver_name.isnot(None),
                Order.driver_name != "",
            )
            .group_by(Order.driver_name)
            .order_by(text("cnt DESC"))
            .limit(limit)
        )
        return [(row.driver_name, row.cnt) for row in result.all()]

    async def all_orders_for_export(self) -> list:
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.hotel),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all() # type: ignore
