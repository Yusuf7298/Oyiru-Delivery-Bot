from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import SUPER_ADMIN_IDS # type: ignore
from database.repositories.user_repository import UserRepository

ROLE_ALIASES = {
    "hotel": {"hotel", "hotel_admin"},
    "hotel_admin": {"hotel", "hotel_admin"},
    "delivery": {"delivery", "driver"},
    "driver": {"delivery", "driver"},
    "store_manager": {"store_manager"},
    "customer": {"customer"},
    "admin": {"admin"},
}

class RoleFilter(BaseFilter):
    def __init__(self, allowed_roles: list[str]) -> None:
        expanded = set()
        for r in allowed_roles:
            norm = r.lower().strip()
            expanded.update(ROLE_ALIASES.get(norm, {norm}))
        self.allowed_roles = expanded

    async def __call__(
        self,
        event: Union[Message, CallbackQuery],
        session: AsyncSession,
    ) -> bool:
        if not event.from_user:
            return False
        # Any super admin passes all admin-role checks
        if "admin" in self.allowed_roles and str(event.from_user.id) in SUPER_ADMIN_IDS:
            return True
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(event.from_user.id)
        if user is None:
            return False
        if not user.is_active:
            return False

        user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        return user_role_str.lower().strip() in self.allowed_roles


class IsAdmin(RoleFilter):
    def __init__(self) -> None:
        super().__init__(["admin"])

class IsHotelAdmin(RoleFilter):
    def __init__(self) -> None:
        super().__init__(["hotel_admin"])

class IsStoreManager(RoleFilter):
    def __init__(self) -> None:
        super().__init__(["store_manager"])

class IsDelivery(RoleFilter):
    def __init__(self) -> None:
        super().__init__(["driver"])

class IsCustomer(RoleFilter):
    def __init__(self) -> None:
        super().__init__(["customer"])

class IsStoreManagerOrAdmin(RoleFilter):
    def __init__(self) -> None:
        super().__init__(["store_manager", "admin"])

