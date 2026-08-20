from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Dict, Optional, Any
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
    def __init__(self, session: Any):
        self.session = session
        self.db = session

    async def _count_orders(self, since: Optional[datetime] = None, status: Optional[Any] = None) -> int:
        query: Dict[str, Any] = {}
        if since:
            query["created_at"] = {"$gte": since}
        if status:
            query["status"] = status.value if hasattr(status, "value") else str(status)
        return await self.db["orders"].count_documents(query)

    async def orders_today(self) -> int:
        return await self._count_orders(since=_start_of_day(_now_utc()))

    async def orders_this_week(self) -> int:
        return await self._count_orders(since=_start_of_week(_now_utc()))

    async def orders_this_month(self) -> int:
        return await self._count_orders(since=_start_of_month(_now_utc()))

    async def orders_total(self) -> int:
        return await self._count_orders()

    async def count_by_status(self) -> dict:
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        cursor = self.db["orders"].aggregate(pipeline)
        result = {}
        async for doc in cursor:
            if doc["_id"]:
                result[str(doc["_id"])] = doc["count"]
        return result

    async def avg_delivery_minutes(self) -> Optional[float]:
        query = {
            "status": OrderStatus.DELIVERED.value,
            "accepted_at": {"$ne": None},
            "delivered_at": {"$ne": None}
        }
        cursor = self.db["orders"].find(query)
        durations = []
        async for doc in cursor:
            acc = doc.get("accepted_at")
            deliv = doc.get("delivered_at")
            if acc and deliv and deliv > acc:
                diff = (deliv - acc).total_seconds() / 60.0
                durations.append(diff)
        return round(sum(durations) / len(durations), 1) if durations else None

    async def top_hotels(self, limit: int = 5) -> List[Tuple[str, int]]:
        pipeline = [
            {"$group": {"_id": "$hotel_id", "cnt": {"$sum": 1}}},
            {"$sort": {"cnt": -1}},
            {"$limit": limit}
        ]
        cursor = self.db["orders"].aggregate(pipeline)
        results = []
        async for doc in cursor:
            hotel_id = doc["_id"]
            cnt = doc["cnt"]
            h_doc = await self.db["hotels"].find_one({"_id": hotel_id})
            name = h_doc["name"] if h_doc else f"Hotel #{hotel_id}"
            results.append((name, cnt))
        return results

    async def top_products(self, limit: int = 5) -> List[Tuple[str, float, str]]:
        pipeline = [
            {"$group": {"_id": "$product_id", "total_qty": {"$sum": "$quantity"}}},
            {"$sort": {"total_qty": -1}},
            {"$limit": limit}
        ]
        cursor = self.db["order_items"].aggregate(pipeline)
        results = []
        async for doc in cursor:
            product_id = doc["_id"]
            total_qty = doc["total_qty"]
            p_doc = await self.db["products"].find_one({"_id": product_id})
            if p_doc:
                results.append((p_doc["name"], total_qty, p_doc.get("unit", "KG")))
        return results

    async def top_drivers(self, limit: int = 5) -> List[Tuple[str, int]]:
        query = {
            "status": OrderStatus.DELIVERED.value,
            "driver_name": {"$exists": True, "$ne": None, "$ne": ""}
        }
        pipeline = [
            {"$match": query},
            {"$group": {"_id": "$driver_name", "cnt": {"$sum": 1}}},
            {"$sort": {"cnt": -1}},
            {"$limit": limit}
        ]
        cursor = self.db["orders"].aggregate(pipeline)
        results = []
        async for doc in cursor:
            results.append((doc["_id"], doc["cnt"]))
        return results

    async def all_orders_for_export(self) -> List[Order]:
        from database.repositories.order_repository import OrderRepository
        order_repo = OrderRepository(self.db)
        cursor = self.db["orders"].find({}).sort("created_at", -1)
        orders = []
        async for doc in cursor:
            order = await order_repo._populate_order(Order.from_dict(doc))
            if order:
                orders.append(order)
        return orders
