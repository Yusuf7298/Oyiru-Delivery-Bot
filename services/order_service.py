from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from database.models.order import Order
from database.models.order_item import OrderItem
from database.repositories.order_repository import OrderRepository
from database.repositories.order_item_repository import OrderItemRepository
from utils.helpers import generate_order_number
from loguru import logger

class OrderService:
    def __init__(self, session: Any):
        self.session = session
        self.repo = OrderRepository(session)
        self.item_repo = OrderItemRepository(session)

    async def create_order(
        self,
        customer_id: int,
        hotel_id: int,
        items: Optional[List[Dict[str, Any]]] = None,
        note: Optional[str] = None,
        file_path: Optional[str] = None,
        telegram_file_id: Optional[str] = None,
        file_type: Optional[str] = None,
        original_filename: Optional[str] = None,
        uploaded_at: Optional[Any] = None,
    ) -> Order:
        order = Order(
            customer_id=customer_id,
            hotel_id=hotel_id,
            note=note,
            file_path=file_path,
            telegram_file_id=telegram_file_id,
            file_type=file_type,
            original_filename=original_filename,
            uploaded_at=(
                datetime.fromisoformat(uploaded_at)
                if uploaded_at and isinstance(uploaded_at, str)
                else uploaded_at
            ),
            order_number="PENDING",
        )

        saved_order = await self.repo.create_order(order)
        saved_order.order_number = generate_order_number(saved_order.id)
        await self.repo.add(saved_order)

        if items:
            for item_data in items:
                order_item = OrderItem(
                    order_id=saved_order.id,
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                )
                await self.item_repo.create_item(order_item)

        loaded_order = await self.repo.get_order(saved_order.id)
        logger.info(
            f"Order {loaded_order.order_number if loaded_order else saved_order.order_number} "
            f"created for customer {customer_id} (Hotel: {hotel_id}). "
            f"Type: {'Upload' if file_path else 'Category'}"
        )

        return loaded_order or saved_order
