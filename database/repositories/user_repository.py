from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models.user import User
from database.repositories.base_repository import BaseRepository
class UserRepository(BaseRepository):
    def __init__(self, session):
        self.session = session
    async def create_user(self, user: User):
        return await self.add(user)
    
    async def get_customers(self):
        result = await self.session.execute(
            select(User).where(User.role == "customer"))
        return result.scalars().all()
    
    async def get_by_role(self, role: str):
        result = await self.session.execute(
            select(User).where(User.role == role))
        return result.scalars().all()
    
    async def get_by_telegram_id(self,telegram_id: int,):
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.hotel))
            .where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()
    
    async def get_delivery_users(self):
        result = await self.session.execute(
            select(User)
                .where(
                    User.role == "delivery",
                    User.is_active == True,
                    )
                .order_by(User.full_name))
        return result.scalars().all()