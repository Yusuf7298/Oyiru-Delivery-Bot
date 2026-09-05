from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repository import UserRepository
from keyboards.customers import customer_menu
from keyboards.delivery import delivery_menu
from keyboards.store_manager import store_manager_menu
from keyboards.admin_menu import admin_main_menu

router = Router()

_KNOWN_BUTTONS = {
    # Customer Place Order
    "🛒 Place Order", "🛒 ትዕዛዝ ያስገቡ", "🛒 Ajaja Galchuu",
    # Customer View Orders
    "📦 My Orders", "📦 View Orders", "📦 የኔ ትዕዛዞች", "📦 Ajajawwan Koo",
    # Customer Reorder
    "🔄 Reorder Last Order", "🔄 Repeat Last Order", "🔄 ያለፈውን ትዕዛዝ ድገም", "🔄 Ajaja Darbe Irra Deebi'i",
    # Customer Category Order
    "🧺 Category Order", "🧺 New Category Order", "🧺 የዕቃዎች ምድብ", "🧺 Kutaalee Mi'aa",
    # Customer Upload List
    "📄 Upload Product List", "📄 Upload New Product List", "📄 የዕቃ ዝርዝር ላክ", "📄 Tarree Mi'aa Ergi",
    # Customer Report Returns
    "📦 Report Returned Products", "📦 Report Returns", "📦 የተመለሱ ዕቃዎችን ሪፖርት አድርግ", "📦 Mi'a Deebi'e Gabaasi",
    # Customer Profile & Help & Language
    "👤 Profile", "👤 My Profile", "👤 መገለጫ", "👤 መገለጫዬ", "👤 Profaayilii Koo",
    "❓ Help", "❓ እርዳታ", "❓ Gargaarsa",
    "💬 Feedback", "💬 አስተያየት", "💬 Yaada",
    "🌐 Language", "🌐 ቋንቋ / Language", "🌐 Afaan / Language", "🌐 Language / ቋንቋ / Afaan",
    # Delivery
    "📦 Available Deliveries", "📦 Geessituuwwan Argaman", "📦 ያሉ ማድረሻዎች",
    "🚚 My Deliveries", "🚚 የኔ ማድረሻዎች", "🚚 Geessituuwwan Koo",
    "📜 Delivery History", "📜 የትዕዛዝ ታሪክ", "📜 Seenaa Geessituu",
    # Store Manager
    "📥 New Orders", "📥 አዳዲስ ትዕዛዞች", "📥 Ajajawwan Haaraa",
    "📦 Active Orders", "📦 የሚሰሩ ትዕዛዞች", "📦 Ajajawwan Hojii Irra Jiran",
    "📜 Order History",
    # Admin
    "🚚 Assign Driver", "📊 Statistics",
}

_ROLE_MENU = {
    "customer": ("Customer Menu", customer_menu),
    "delivery": ("Delivery Menu", delivery_menu),
    "hotel":    ("Store Manager Menu", store_manager_menu),
    "admin":    ("Admin Menu", admin_main_menu),
}


from keyboards.store_manager import store_manager_menu, hotel_admin_menu

@router.message(F.text.in_(_KNOWN_BUTTONS))
async def fallback_known_button(message: Message, session: AsyncSession):
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

    user_lang = getattr(user, "language", "en") or "en"
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    
    if role_val in ("driver", "delivery"):
        await message.answer(
            "ℹ️ Main Menu:",
            reply_markup=delivery_menu(user_lang),
        )
    elif role_val in ("hotel_admin", "hotel"):
        await message.answer(
            "ℹ️ Main Menu:",
            reply_markup=hotel_admin_menu(user_lang),
        )
    elif role_val == "store_manager":
        await message.answer(
            "ℹ️ Main Menu:",
            reply_markup=store_manager_menu(user_lang),
        )
    elif role_val == "admin":
        await message.answer(
            "ℹ️ Main Menu:",
            reply_markup=admin_main_menu(user_lang),
        )
    else:
        await message.answer(
            "ℹ️ Main Menu:",
            reply_markup=customer_menu(user_lang),
        )

