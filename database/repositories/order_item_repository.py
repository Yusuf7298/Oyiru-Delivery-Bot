from typing import Any
from database.models.order_item import OrderItem
from database.repositories.base_repository import BaseRepository

class OrderItemRepository(BaseRepository):
    def __init__(self, session: Any):
        super().__init__(session)

    async def create_item(self, item: OrderItem) -> OrderItem:
        return await self.add(item)
