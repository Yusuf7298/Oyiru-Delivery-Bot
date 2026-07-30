from database.models.order import Order
from database.models.order_item import OrderItem
from database.repositories.order_repository import OrderRepository
from utils.helpers import generate_order_number
from loguru import logger


class OrderService:
    def __init__(self, session):
        self.session = session
        self.repo = OrderRepository(session)

    async def create_order(
        self,
        customer_id: int,
        hotel_id: int,
        items: list = None, # type: ignore
        note: str = None, # type: ignore
        file_path: str = None, # type: ignore
        telegram_file_id: str = None, # type: ignore
        file_type: str = None, # type: ignore
        original_filename: str = None, # type: ignore
        uploaded_at: str = None, # type: ignore
    ) -> Order:
        from datetime import datetime, timezone

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

        self.session.add(order)
        await self.session.flush()

        # Generate order number from the now-known id
        order.order_number = generate_order_number(order.id)

        # Add all order items in the same transaction
        if items:
            for item_data in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                )
                self.session.add(order_item)

        # Single atomic commit — all rows or none
        await self.session.commit()

        loaded_order = await self.repo.get_order(order.id)
        logger.info(
            f"Order {loaded_order.order_number} created for customer {customer_id} "
            f"(Hotel: {hotel_id}). Type: {'Upload' if file_path else 'Category'}"
        )

        return loaded_order
