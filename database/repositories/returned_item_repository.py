from sqlalchemy import select
from database.models.returned_item import ReturnedItem
from database.repositories.base_repository import BaseRepository


class ReturnedItemRepository(BaseRepository):

    async def create(self, returned_item: ReturnedItem) -> ReturnedItem:
        return await self.add(returned_item)

    async def get_by_order(self, order_id: int) -> list[ReturnedItem]:
        result = await self.session.execute(
            select(ReturnedItem)
            .where(ReturnedItem.order_id == order_id)
            .order_by(ReturnedItem.created_at)
        )
        return result.scalars().all() # type: ignore
