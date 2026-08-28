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
from keyboards.store_manager import hotel_admin_menu, store_manager_menu
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
    if not user and message.from_user.username:
        pre_user = await user_repo.get_by_username(message.from_user.username)
        if pre_user and (not pre_user.telegram_id or pre_user.telegram_id == message.from_user.id):
            pre_user.telegram_id = message.from_user.id
            pre_user.username = message.from_user.username
            await user_repo.add(pre_user)
            user = pre_user

    if user:
        if message.from_user.username and message.from_user.username != user.username:
            user.username = message.from_user.username
            await user_repo.update_username(user.telegram_id, user.username)
        user_lang = getattr(user, "language", lang) or lang
        await _show_user_menu(message, user, session, lang=user_lang)
        return

    # Check for deep-link payload e.g. "/start join_3" or "/start hotel_3"
    args = (message.text or "").strip().split()
    payload = args[1] if len(args) > 1 else None

    from database.repositories.hotel_repository import HotelRepository
    from states.registration import RegistrationState
    hotel_repo = HotelRepository(session)

    if payload and payload in ("driver", "driver_join", "join_driver"):
        await state.update_data(hotel_id=None, is_driver_register=True, is_hotel_admin=False, is_staff_invite=False)
        await state.set_state(RegistrationState.full_name)
        await message.answer(
            "🚚 *Welcome to Oyiru Delivery Driver Registration!*\n\n"
            "Please enter your *full name* to start registration:",
            parse_mode="Markdown"
        )
        return

    if payload and (payload.startswith("join_") or payload.startswith("hotel_")):
        raw_id = payload.replace("join_", "").replace("hotel_", "")
        if raw_id.isdigit():
            hotel_id = int(raw_id)
            hotel = await hotel_repo.get_by_id(hotel_id)
            if hotel and hotel.is_active:
                await state.update_data(hotel_id=hotel_id, is_staff_invite=True, is_hotel_admin=False)
                await state.set_state(RegistrationState.full_name)
                await message.answer(
                    t("staff_invite_registered", lang, hotel_name=hotel.name),
                    parse_mode="Markdown"
                )
                return

    # Normal registration: Show only unclaimed active hotels so once a hotel is registered, it doesn't show to others
    claimed_ids = await user_repo.get_claimed_hotel_ids()
    available_hotels = await hotel_repo.get_unclaimed_active_hotels(claimed_ids)

    if not available_hotels:
        await message.answer(
            t("no_unclaimed_hotels_msg", lang),
            parse_mode="Markdown"
        )
        return

    await message.answer(
        t("select_hotel_title", lang),
        reply_markup=hotels_keyboard(available_hotels),
        parse_mode="Markdown"
    )


async def _show_user_menu(message: Message, user, session: AsyncSession, lang: str = "en") -> None:
    user_lang = getattr(user, "language", lang) or lang
    if not user.is_active:
        await message.answer(t("reg_pending", user_lang))
        return

    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)

    if role_val == "customer":
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

    elif role_val in ("hotel_admin", "hotel"):
        hotel_name = user.hotel.name if getattr(user, "hotel", None) else "Hotel"
        await message.answer(
            t("welcome_hotel_admin", user_lang, name=user.full_name, hotel_name=hotel_name),
            reply_markup=hotel_admin_menu(user_lang),
            parse_mode="Markdown"
        )

    elif role_val == "store_manager":
        await message.answer(
            f"🏪 *Welcome Store Manager, {user.full_name}!*",
            reply_markup=store_manager_menu(user_lang),
            parse_mode="Markdown"
        )

    elif role_val in ("driver", "delivery"):
        await message.answer(
            t("welcome_user", user_lang, name=user.full_name),
            reply_markup=delivery_menu(user_lang),
        )

    elif role_val == "admin":
        await message.answer(
            t("welcome_admin", user_lang, name=user.full_name),
            reply_markup=admin_main_menu(user_lang),
        )

    else:
        await message.answer(
            t("welcome_user", user_lang, name=user.full_name),
            reply_markup=customer_menu(user_lang),
        )
