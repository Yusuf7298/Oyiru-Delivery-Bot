from datetime import datetime, timezone
from typing import List, Optional, Any, Tuple, Dict
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem
from database.models.product import Product
from database.models.user import User
from database.models.hotel import Hotel
from database.repositories.base_repository import BaseRepository

class OrderRepository(BaseRepository):
    def __init__(self, session: Any):
        super().__init__(session)

    async def _populate_order(self, order: Optional[Order]) -> Optional[Order]:
        if not order:
            return None
        if order.customer_id and not order.customer:
            c_doc = await self.db["users"].find_one({"_id": order.customer_id})
            if c_doc:
                order.customer = User.from_dict(c_doc)
        if order.hotel_id and not order.hotel:
            h_doc = await self.db["hotels"].find_one({"_id": order.hotel_id})
            if h_doc:
                order.hotel = Hotel.from_dict(h_doc)
        if order.delivery_partner_id and not order.delivery_partner:
            d_doc = await self.db["users"].find_one({"_id": order.delivery_partner_id})
            if d_doc:
                order.delivery_partner = User.from_dict(d_doc)
        if getattr(order, "id", None):
            cursor = self.db["order_items"].find({"order_id": order.id})
            items = []
            async for item_doc in cursor:
                item = OrderItem.from_dict(item_doc)
                if item.product_id and not item.product:
                    p_doc = await self.db["products"].find_one({"_id": item.product_id})
                    if p_doc:
                        item.product = Product.from_dict(p_doc)
                if not item.product:
                    p_name = item.product_name or item_doc.get("product_name") or "Product"
                    p_unit = item.unit or item_doc.get("unit") or "KG"
                    item.product = Product(id=item.product_id or 0, name=p_name, unit=p_unit)
                items.append(item)
            order.items = items
        return order

    async def create_order(self, order: Order) -> Order:
        created = await self.add(order)
        return await self._populate_order(created) # type: ignore

    async def get_order(self, order_id: int) -> Optional[Order]:
        doc = await self.db["orders"].find_one({"_id": order_id})
        if not doc:
            return None
        return await self._populate_order(Order.from_dict(doc))

    async def get_by_number(self, order_number: str) -> Optional[Order]:
        doc = await self.db["orders"].find_one({"order_number": order_number})
        if not doc:
            return None
        return await self._populate_order(Order.from_dict(doc))

    async def pending_orders(self) -> List[Order]:
        cursor = self.db["orders"].find({"status": OrderStatus.SUBMITTED.value}).sort("created_at", 1)
        orders = []
        async for doc in cursor:
            order = await self._populate_order(Order.from_dict(doc))
            if order:
                orders.append(order)
        return orders

    async def get_approved_no_driver(self) -> List[Order]:
        cursor = self.db["orders"].find({
            "status": OrderStatus.APPROVED.value,
            "$or": [{"delivery_partner_id": None}, {"delivery_partner_id": {"$exists": False}}]
        }).sort("created_at", 1)
        orders = []
        async for doc in cursor:
            order = await self._populate_order(Order.from_dict(doc))
            if order:
                orders.append(order)
        return orders

    async def get_active_orders_all(self) -> List[Order]:
        statuses = [
            OrderStatus.APPROVED.value,
            OrderStatus.PREPARING.value,
            OrderStatus.PACKED.value,
            OrderStatus.OUT_FOR_DELIVERY.value,
        ]
        cursor = self.db["orders"].find({"status": {"$in": statuses}}).sort("created_at", -1)
        orders = []
        async for doc in cursor:
            order = await self._populate_order(Order.from_dict(doc))
            if order:
                orders.append(order)
        return orders

    async def get_new_orders(self, hotel_id: int) -> List[Order]:
        cursor = self.db["orders"].find({
            "hotel_id": hotel_id,
            "status": OrderStatus.SUBMITTED.value
        }).sort("created_at", -1)
        orders = []
        async for doc in cursor:
            order = await self._populate_order(Order.from_dict(doc))
            if order:
                orders.append(order)
        return orders

    async def get_active_orders(self, hotel_id: int) -> List[Order]:
        statuses = [
            OrderStatus.APPROVED.value,
            OrderStatus.PREPARING.value,
            OrderStatus.PACKED.value,
            OrderStatus.OUT_FOR_DELIVERY.value,
        ]
        cursor = self.db["orders"].find({
            "hotel_id": hotel_id,
            "status": {"$in": statuses}
        }).sort("created_at", -1)
        orders = []
        async for doc in cursor:
            order = await self._populate_order(Order.from_dict(doc))
            if order:
                orders.append(order)
        return orders

    async def get_order_history(self, hotel_id: int) -> List[Order]:
        statuses = [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]
        cursor = self.db["orders"].find({
            "hotel_id": hotel_id,
            "status": {"$in": statuses}
        }).sort("created_at", -1).limit(50)
        orders = []
        async for doc in cursor:
            order = await self._populate_order(Order.from_dict(doc))
            if order:
                orders.append(order)
        return orders

    async def get_last_order(self, customer_id: int) -> Optional[Order]:
        cursor = self.db["orders"].find({"customer_id": customer_id}).sort("created_at", -1).limit(1)
        async for doc in cursor:
            return await self._populate_order(Order.from_dict(doc))
        return None

    async def get_customer_orders(self, customer_id: int) -> List[Order]:
        cursor = self.db["orders"].find({"customer_id": customer_id}).sort("created_at", -1)
        orders = []
        async for doc in cursor:
            order = await self._populate_order(Order.from_dict(doc))
            if order:
                orders.append(order)
        return orders

    async def get_hotel_all_orders(self, hotel_id: int) -> List[Order]:
        cursor = self.db["orders"].find({"hotel_id": hotel_id}).sort("created_at", -1)
        orders = []
        async for doc in cursor:
            order = await self._populate_order(Order.from_dict(doc))
            if order:
                orders.append(order)
        return orders

    async def get_hotel_by_telegram(self, telegram_id: int) -> Optional[User]:
        doc = await self.db["users"].find_one({"telegram_id": telegram_id})
        if not doc:
            return None
        user = User.from_dict(doc)
        if user.hotel_id:
            h_doc = await self.db["hotels"].find_one({"_id": user.hotel_id})
            if h_doc:
                user.hotel = Hotel.from_dict(h_doc)
        return user

    async def get_driver_orders(self, driver_id: int) -> Dict[str, List[Order]]:
        async def _fetch(statuses: List[str]) -> List[Order]:
            cursor = self.db["orders"].find({
                "delivery_partner_id": driver_id,
                "status": {"$in": statuses}
            }).sort("created_at", -1)
            orders = []
            async for doc in cursor:
                order = await self._populate_order(Order.from_dict(doc))
                if order:
                    orders.append(order)
            return orders

        return {
            "assigned": await _fetch([OrderStatus.APPROVED.value]),
            "accepted": await _fetch([OrderStatus.OUT_FOR_DELIVERY.value]),
            "completed": await _fetch([OrderStatus.DELIVERED.value]),
        }

    async def approve_order(self, order_id: int, driver_name: str) -> Tuple[Optional[Order], str]:
        order = await self.get_order(order_id)
        if not order:
            return None, "not_found"
        if order.status != OrderStatus.SUBMITTED.value and order.status != OrderStatus.SUBMITTED:
            return order, "already_processed"
        order.status = OrderStatus.APPROVED.value
        order.driver_name = driver_name.strip()
        await self.add(order)
        return await self.get_order(order_id), "ok"

    async def reject_order(self, order_id: int, reason: str) -> Tuple[Optional[Order], str]:
        order = await self.get_order(order_id)
        if not order:
            return None, "not_found"
        if order.status != OrderStatus.SUBMITTED.value and order.status != OrderStatus.SUBMITTED:
            return order, "already_processed"
        order.status = OrderStatus.CANCELLED.value
        existing = order.note or ""
        order.note = (
            f"[REJECTED: {reason.strip()}]"
            + (f" — {existing}" if existing else "")
        )
        await self.add(order)
        return await self.get_order(order_id), "ok"

    async def assign_driver(self, order_id: int, driver_id: int) -> Tuple[Optional[Order], str]:
        order = await self.get_order(order_id)
        if not order:
            return None, "not_found"
        if order.status not in (OrderStatus.SUBMITTED.value, OrderStatus.SUBMITTED, OrderStatus.APPROVED.value, OrderStatus.APPROVED):
            return order, "not_approved"
        if order.delivery_partner_id is not None:
            return order, "already_assigned"
        order.delivery_partner_id = driver_id
        if order.status == OrderStatus.SUBMITTED.value or order.status == OrderStatus.SUBMITTED:
            order.status = OrderStatus.APPROVED.value
        await self.add(order)
        return await self.get_order(order_id), "ok"

    async def update_order_status(self, order_id: int, status: Any) -> Optional[Order]:
        order = await self.get_order(order_id)
        if order:
            status_val = status.value if hasattr(status, "value") else str(status)
            order.status = status_val
            if status_val == OrderStatus.DELIVERED.value:
                order.delivered_at = datetime.now(timezone.utc)
            await self.add(order)
            return await self.get_order(order_id)
        return order

    async def pending_assignment_orders(self) -> List[Order]:
        return await self.pending_orders()

    async def assign_internal_driver(self, order_id: int, driver_name: str) -> Optional[Order]:
        order, _ = await self.approve_order(order_id, driver_name)
        return order

    async def accept_order(self, order_id: int) -> Optional[Order]:
        return await self.update_order_status(order_id, OrderStatus.OUT_FOR_DELIVERY)

    async def driver_accept(self, order_id: int, driver_id: int) -> Tuple[Optional[Order], str]:
        order = await self.get_order(order_id)
        if not order:
            return None, "not_found"
        if order.delivery_partner_id != driver_id:
            return order, "not_assigned"
        valid_statuses = (
            OrderStatus.APPROVED.value, OrderStatus.APPROVED,
            OrderStatus.PREPARING.value, OrderStatus.PREPARING,
            OrderStatus.PACKED.value, OrderStatus.PACKED
        )
        if order.status not in valid_statuses:
            return order, "wrong_status"
        order.status = OrderStatus.OUT_FOR_DELIVERY.value
        order.accepted_at = datetime.now(timezone.utc)
        await self.add(order)
        return await self.get_order(order_id), "ok"

    async def driver_complete(self, order_id: int, driver_id: int) -> Tuple[Optional[Order], str]:
        order = await self.get_order(order_id)
        if not order:
            return None, "not_found"
        if order.delivery_partner_id != driver_id:
            return order, "not_assigned"
        if order.status != OrderStatus.OUT_FOR_DELIVERY.value and order.status != OrderStatus.OUT_FOR_DELIVERY:
            return order, "wrong_status"
        order.status = OrderStatus.DELIVERED.value
        order.delivered_at = datetime.now(timezone.utc)
        await self.add(order)
        return await self.get_order(order_id), "ok"
