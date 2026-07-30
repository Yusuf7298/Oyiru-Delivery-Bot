from database.models.order_item import OrderItem
from database.repositories.base_repository import BaseRepository

class OrderItemRepository(BaseRepository):
    async def create_item(self, item: OrderItem):
        return await self.add(item)
