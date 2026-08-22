from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import SUPER_ADMIN_IDS # type: ignore
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
from utils.i18n import t

router = Router()

@router.message(CommandStart())
async def start(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en") -> None:
    await state.clear()
    assert message.from_user is not None

    if str(message.from_user.id) in SUPER_ADMIN_IDS:
        await message.answer(
            t("welcome_admin", lang, name="Admin"),
            reply_markup=admin_main_menu(lang),
            parse_mode="Markdown",
        )
        return

    user_repo = UserRepository(session)
    auth = AuthService(user_repo)
    user = await auth.user_exists(message.from_user.id)
    if user:
        user_lang = getattr(user, "language", lang) or lang
        await _show_user_menu(message, user, session, lang=user_lang)
        return
    hotel_service = HotelService(session)
    hotels = await hotel_service.get_hotels()
    if not hotels:
        await message.answer(t("no_hotels", lang))
        return

    await message.answer(
        t("select_hotel", lang),
        reply_markup=hotels_keyboard(hotels),
    )


async def _show_user_menu(message: Message, user, session: AsyncSession, lang: str = "en") -> None:
    user_lang = getattr(user, "language", lang) or lang
    if not user.is_active:
        await message.answer(t("reg_pending", user_lang))
        return

    if user.role == UserRole.CUSTOMER:
        order_repo = OrderRepository(session)
        last_order = await order_repo.get_last_order(user.id)
        if last_order:
            await message.answer(
                t("welcome_back", user_lang, name=user.full_name),
                reply_markup=customer_reorder_menu(user_lang),
            )
        else:
            await message.answer(
                t("welcome_back", user_lang, name=user.full_name),
                reply_markup=customer_menu(user_lang),
            )

    elif user.role == UserRole.HOTEL:
        await message.answer(
            t("welcome_user", user_lang, name=user.full_name),
            reply_markup=store_manager_menu(user_lang),
        )

    elif user.role == UserRole.DELIVERY:
        await message.answer(
            t("welcome_user", user_lang, name=user.full_name),
            reply_markup=delivery_menu(user_lang),
        )

    elif user.role == UserRole.ADMIN:
        await message.answer(
            t("welcome_admin", user_lang, name=user.full_name),
            reply_markup=admin_main_menu(user_lang),
        )

    else:
        await message.answer(
            t("welcome_user", user_lang, name=user.full_name)
        )

