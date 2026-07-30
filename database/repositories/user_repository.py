from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models.user import User, UserRole
from database.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session):
        self.session = session
    async def create_user(self, user: User):
        return await self.add(user)

    async def get_customers(self):
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.hotel))
            .where(User.role == UserRole.CUSTOMER)
            .order_by(User.full_name)
        )
        return result.scalars().all()

    async def get_by_role(self, role: str):
        result = await self.session.execute(
            select(User)
            .where(User.role == role)
            .order_by(User.full_name)
        )
        return result.scalars().all()

    async def get_by_telegram_id(self, telegram_id: int):
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.hotel))
            .where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_delivery_partners(self):
        result = await self.session.execute(
            select(User)
            .where(
                User.role == UserRole.DELIVERY,
                User.is_active == True,
            )
            .order_by(User.full_name)
        )
        return result.scalars().all()

    async def get(self, user_id: int):
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all_users(self):
        result = await self.session.execute(
            select(User).order_by(User.role, User.full_name)
        )
        return result.scalars().all()

    async def set_role(self, user: User, role: str):
        user.role = role
        user.is_active = True
        await self.session.commit()
        return user

    async def set_active(self, user: User, active: bool):
        user.is_active = active
        await self.session.commit()
        return user

    async def get_active_by_roles(self, roles: list) -> list:
        """Return all active users matching any of the given roles."""
        result = await self.session.execute(
            select(User)
            .where(User.role.in_(roles), User.is_active == True)
            .order_by(User.role, User.full_name)
        )
        return result.scalars().all() # type: ignore
