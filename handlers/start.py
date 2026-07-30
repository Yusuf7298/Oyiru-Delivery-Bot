from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import ADMIN_ID # type: ignore
from services.auth_service import AuthService
from services.hotel_service import HotelService
from database.models.user import UserRole
from database.repositories.user_repository import UserRepository
from database.repositories.order_repository import OrderRepository
from keyboards.customer.hotel_keyboard import hotels_keyboard
from keyboards.customers import customer_menu, customer_reorder_menu
from keyboards.store_manager import store_manager_menu
from keyboards.admin_menu import admin_main_menu
from keyboards.delivery import delivery_menu

router = Router()

@router.message(CommandStart())
async def start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    assert message.from_user is not None

    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer(
            "👑 Welcome Admin!\n\n"
            "Use /admin to open the admin panel.",
            reply_markup=admin_main_menu(),
            parse_mode="Markdown",
        )
        return

    user_repo = UserRepository(session)
    auth = AuthService(user_repo)
    user = await auth.user_exists(message.from_user.id)
    if user:
        await _show_user_menu(message, user, session)
        return
    hotel_service = HotelService(session)
    hotels = await hotel_service.get_hotels()
    if not hotels:
        await message.answer(
            "❌ No hotels are available at the moment.\n"
            "Please contact the administrator."
        )
        return

    await message.answer(
        "🏨 Welcome to Oyiru!\n\n"
        "Please select your hotel to begin registration.",
        reply_markup=hotels_keyboard(hotels),  # type: ignore
    )


async def _show_user_menu(message: Message, user, session: AsyncSession) -> None:
    if not user.is_active:
        await message.answer(
            "⏳ Your registration is pending approval by the administrator.\n"
            "You will be notified once approved."
        )
        return
    if user.role == UserRole.CUSTOMER:
        order_repo = OrderRepository(session)
        last_order = await order_repo.get_last_order(user.id)
        if last_order:
            await message.answer(
                f"👋 Welcome back, {user.full_name}!",
                reply_markup=customer_reorder_menu(),
            )
        else:
            await message.answer(
                f"👋 Welcome back, {user.full_name}!",
                reply_markup=customer_menu(),
            )

    elif user.role == UserRole.HOTEL:
        await message.answer(
            f"👋 Welcome, {user.full_name}!",
            reply_markup=store_manager_menu(),
        )

    elif user.role == UserRole.DELIVERY:
        await message.answer(
            f"🚛 Welcome, {user.full_name}!",
            reply_markup=delivery_menu(),
        )

    elif user.role == UserRole.ADMIN:
        await message.answer(
            f"👑 Welcome Admin, {user.full_name}!\n\nUse /admin to open the admin panel.",
            reply_markup=admin_main_menu(),
        )

    else:
        await message.answer(
            f"👋 Welcome, {user.full_name}!\nRole: {user.role}"
        )
