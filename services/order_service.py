from database.repositories.order_repository import OrderRepository
class OrderService:
    def __init__(self, session):
        self.repo = OrderRepository(session)
    async def create_order(self,customer_id,hotel_id,items, note=None,
    ):
        return await self.repo.create_order(
            customer_id=customer_id,
            hotel_id=hotel_id,
            items=items,
            note=note,
        )