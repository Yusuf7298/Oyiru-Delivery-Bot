import logging
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import ADMIN_ID # type: ignore
from database.models.user import User
from database.repositories.user_repository import UserRepository
from services.auth_service import AuthService
from states.registration import RegistrationState
router = Router()


@router.message(RegistrationState.full_name)
async def handle_full_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name or len(name) < 2:
        await message.answer("❌ Please enter a valid full name (at least 2 characters):")
        return
    if len(name) > 150:
        await message.answer("❌ Name is too long (max 150 characters):")
        return
    await state.update_data(full_name=name)
    await message.answer("📱 Enter your phone number:")
    await state.set_state(RegistrationState.phone)


@router.message(RegistrationState.phone)
async def handle_phone(message: Message, state: FSMContext, session: AsyncSession) -> None:
    phone = (message.text or "").strip()
    if not phone or len(phone) < 7:
        await message.answer("❌ Please enter a valid phone number (at least 7 digits):")
        return
    if len(phone) > 20:
        await message.answer("❌ Phone number is too long (max 20 characters):")
        return

    data = await state.get_data()
    hotel_id: int | None = data.get("hotel_id")
    if not hotel_id:
        await state.clear()
        await message.answer(
            "❌ Session expired. Please start again with /start."
        )
        return

    user_repo = UserRepository(session)
    existing = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if existing:
        await state.clear()
        if existing.is_active:
            await message.answer(
                "✅ You are already registered and approved.\n"
                "Use /start to access your menu."
            )
        else:
            await message.answer(
                "⏳ Your registration is already pending approval.\n"
                "Please wait — you will be notified once approved."
            )
        return

    auth = AuthService(user_repo)
    user = await auth.register_user(
        telegram_id=message.from_user.id, # type: ignore
        full_name=data["full_name"],
        username=message.from_user.username, # type: ignore
        phone=phone,
        hotel_id=hotel_id,
        is_active=False,
    )

    await state.clear()
    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_user:{user.id}"),
            InlineKeyboardButton(text="❌ Reject",  callback_data=f"reject_user:{user.id}"),
        ]]
    )

    hotel_name = "—"
    if user.hotel_id:
        from database.repositories.hotel_repository import HotelRepository
        hotel = await HotelRepository(session).get_by_id(user.hotel_id)
        if hotel:
            hotel_name = hotel.name

    try:
        await message.bot.send_message( # type: ignore
            chat_id=int(ADMIN_ID),
            text=(
                "🔔 *New Customer Registration Request*\n\n"
                f"👤 *Name*: {data['full_name']}\n"
                f"📱 *Phone*: {phone}\n"
                f"🏨 *Hotel*: {hotel_name}\n"
                f"🆔 *Telegram ID*: `{message.from_user.id}`\n" # type: ignore
                f"🏷 *Username*: @{message.from_user.username or 'none'}" # type: ignore
            ),
            reply_markup=admin_keyboard,
            parse_mode="Markdown",
        )
    except Exception as e:
        logging.error(f"Failed to notify admin of registration: {e}")

    await message.answer(
        "📝 Registration submitted!\n\n"
        "Your request is pending approval by the administrator.\n"
        "You will receive a notification once your account is approved.",
        parse_mode="Markdown",
    )
