"""
Fallback handler — catches button presses that don't match any role-filtered handler.
Registered LAST in app.py so it only fires when nothing else matched.
"""

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import UserRole
from database.repositories.user_repository import UserRepository
from keyboards.customers import customer_menu
from keyboards.delivery import delivery_menu
from keyboards.store_manager import store_manager_menu
from keyboards.admin_menu import admin_main_menu

router = Router()

# All known button texts from every role's keyboard
_KNOWN_BUTTONS = {
    # Customer
    "📦 Place Order", "📋 View Orders", "🔄 Report Returned Products", "❓ Help",
    "🔁 Repeat Last Order", "🧺 New Category Order", "📄 Upload New Product List",
    # Delivery
    "📦 Assigned Orders", "📦 Available Deliveries", "🚛 Active Delivery",
    "🚚 My Deliveries", "📜 Delivery History", "👤 My Profile",
    # Store Manager
    "📥 New Orders", "📦 Active Orders", "📜 Order History", "📋 Store Manager",
    # Admin
    "📦 New Orders", "🚚 Assign Driver", "📊 Statistics",
}

_ROLE_MENU = {
    "customer": ("👤 Customer Menu", customer_menu),
    "delivery": ("🚛 Delivery Menu", delivery_menu),
    "hotel":    ("🏪 Store Manager Menu", store_manager_menu),
    "admin":    ("👑 Admin Menu", admin_main_menu),
}


@router.message(F.text.in_(_KNOWN_BUTTONS))
async def fallback_known_button(message: Message, session: AsyncSession):
    """Catches role-mismatched button presses and shows the correct menu."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer(
            "❌ You are not registered yet.\n"
            "Use /start to begin registration."
        )
        return

    if not user.is_active:
        await message.answer(
            "⏳ Your account is pending approval.\n"
            "Please wait for the administrator to approve your registration."
        )
        return

    label, menu_fn = _ROLE_MENU.get(user.role, ("Menu", customer_menu))
    await message.answer(
        f"⚠️ That button is not available for your role.\n\n"
        f"Here is your menu:",
        reply_markup=menu_fn(),
    )
