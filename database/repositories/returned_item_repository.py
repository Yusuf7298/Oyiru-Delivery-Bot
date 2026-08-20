from typing import List, Any
from database.models.returned_item import ReturnedItem
from database.repositories.base_repository import BaseRepository

class ReturnedItemRepository(BaseRepository):
    def __init__(self, session: Any):
        super().__init__(session)

    async def create(self, returned_item: ReturnedItem) -> ReturnedItem:
        return await self.add(returned_item)

    async def get_by_order(self, order_id: int) -> List[ReturnedItem]:
        cursor = self.db["returned_items"].find({"order_id": order_id}).sort("created_at", 1)
        items = []
        async for doc in cursor:
            items.append(ReturnedItem.from_dict(doc))
        return items
