from __future__ import annotations
import logging
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import SUPER_ADMIN_IDS # type: ignore
from database.models.user import User
from database.repositories.user_repository import UserRepository
from services.auth_service import AuthService
from states.registration import RegistrationState
router = Router()


from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from utils.helpers import normalize_ethiopian_phone, format_phone_display
from utils.i18n import t

def share_contact_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    btn_text = "📲 Share Phone Number"
    if lang == "am":
        btn_text = "📲 ስልክ ቁጥርዎን ያጋሩ"
    elif lang == "om":
        btn_text = "📲 Lakkoofsa Bilbilaa Qoodaa"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn_text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@router.message(RegistrationState.full_name)
async def handle_full_name(message: Message, state: FSMContext, lang: str = "en") -> None:
    name = (message.text or "").strip()
    if not name or len(name) < 2:
        await message.answer("❌ Please enter a valid full name (at least 2 characters):")
        return
    if len(name) > 150:
        await message.answer("❌ Name is too long (max 150 characters):")
        return
    await state.update_data(full_name=name)
    
    if lang == "am":
        prompt = (
            "📱 *እባክዎን ስልክ ቁጥርዎን ያስገቡ:*\n"
            "ከታች ያለውን *📲 ስልክ ቁጥርዎን ያጋሩ* የሚለውን ቁልፍ መጫን ወይም በጽሑፍ መላክ ይችላሉ:\n"
            "_(በ `+2519`, `+2517`, `09`, ወይም `07` የሚጀምር 10 ዲጂት)_"
        )
    elif lang == "om":
        prompt = (
            "📱 *Maaloo lakkoofsa bilbilaa keessan galchaa:*\n"
            "Qubsumma *📲 Lakkoofsa Bilbilaa Qoodaa* jedhu cuqaasaa yookiin barreessaa ergaa:\n"
            "_(kan `+2519`, `+2517`, `09`, yookiin `07` tiin jalqabu)_"
        )
    else:
        prompt = (
            "📱 *Please enter your phone number:*\n"
            "You can tap the *📲 Share Phone Number* button below or type it manually:\n"
            "_(Must start with `+2519`, `+2517`, `09`, or `07`)_"
        )

    await message.answer(prompt, reply_markup=share_contact_keyboard(lang=lang), parse_mode="Markdown")
    await state.set_state(RegistrationState.phone)


@router.message(RegistrationState.phone)
async def handle_phone(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en") -> None:
    raw_phone = ""
    if message.contact:
        raw_phone = message.contact.phone_number or ""
    elif message.text:
        raw_phone = message.text.strip()

    normalized_phone = normalize_ethiopian_phone(raw_phone)
    if not normalized_phone:
        if lang == "am":
            err = (
                "❌ *ትክክለኛ ያልሆነ የስልክ ቁጥር!*\n\n"
                "እባክዎን ትክክለኛ የኢትዮጵያ ስልክ ቁጥር ያስገቡ:\n"
                "• በ `+2519`, `+2517`, `09`, ወይም `07` የሚጀምር\n"
                "• ምሳሌ: `0987654321` ወይም `+251987654321`"
            )
        elif lang == "om":
            err = (
                "❌ *Lakkoofsi bilbilaa dogoggora!*\n\n"
                "Maaloo lakkoofsa bilbilaa Itoophiyaa sirrii galchaa:\n"
                "• kan `+2519`, `+2517`, `09`, yookiin `07` tiin jalqabu\n"
                "• Fakkeenya: `0987654321` yookiin `+251987654321`"
            )
        else:
            err = (
                "❌ *Invalid Phone Number!*\n\n"
                "Please enter a valid Ethiopian phone number:\n"
                "• Must start with `+2519`, `+2517`, `09`, or `07`\n"
                "• Example: `0987654321` or `+251987654321`"
            )
        await message.answer(err, reply_markup=share_contact_keyboard(lang=lang), parse_mode="Markdown")
        return

    data = await state.get_data()
    hotel_id: int | None = data.get("hotel_id")
    if not hotel_id:
        await state.clear()
        await message.answer(
            "❌ Session expired. Please start again with /start.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    user_repo = UserRepository(session)
    existing_phone = await user_repo.get_by_phone(normalized_phone)
    if existing_phone and existing_phone.telegram_id != message.from_user.id:
        if lang == "am":
            err = "⚠️ *ይህ የስልክ ቁጥር አስቀድሞ በሌላ ሰው ተመዝግቧል!*\n\nእባክዎን የራስዎን ትክክለኛ እና ልዩ ስልክ ቁጥር ያስገቡ:"
        elif lang == "om":
            err = "⚠️ *Lakkoofsi bilbilaa kun kanaan dura galmaa'eera!*\n\nMaaloo lakkoofsa bilbilaa keessan isa sirrii galchaa:"
        else:
            err = "⚠️ *This phone number is already registered to another account!*\n\nPlease provide your own unique phone number:"
        await message.answer(err, reply_markup=share_contact_keyboard(lang=lang), parse_mode="Markdown")
        return

    existing = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if existing:
        await state.clear()
        if existing.is_active:
            await message.answer(
                "✅ You are already registered and approved.\nUse /start to access your menu.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer(
                "⏳ Your registration is already pending approval.\nPlease wait — you will be notified once approved.",
                reply_markup=ReplyKeyboardRemove()
            )
        return

    is_hotel_admin = data.get("is_hotel_admin", False)
    user_role = "hotel" if is_hotel_admin else "customer"
    role_label = "Hotel Administrator" if is_hotel_admin else "Hotel Ordering Staff"

    auth = AuthService(user_repo)
    user = await auth.register_user(
        telegram_id=message.from_user.id, # type: ignore
        full_name=data["full_name"],
        username=message.from_user.username, # type: ignore
        phone=format_phone_display(normalized_phone),
        hotel_id=hotel_id,
        role=user_role,
        is_active=False,
    )

    await state.clear()
    await message.answer("⏳ Registration submitted! Waiting for approval...", reply_markup=ReplyKeyboardRemove())
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

    import html
    name_clean = html.escape(str(data.get("full_name", "")))
    phone_clean = html.escape(str(phone))
    hotel_clean = html.escape(str(hotel_name))
    uname = html.escape(str(message.from_user.username or "none")) # type: ignore

    try:
        notification_text = (
            f"🔔 <b>New {role_label} Registration Request</b>\n\n"
            f"👤 <b>Name</b>: {name_clean}\n"
            f"📱 <b>Phone</b>: {phone_clean}\n"
            f"🏨 <b>Hotel</b>: {hotel_clean}\n"
            f"🏷 <b>Role</b>: {role_label}\n"
            f"🆔 <b>Telegram ID</b>: <code>{message.from_user.id}</code>\n" # type: ignore
            f"🏷 <b>Username</b>: @{uname}"
        )
        for admin_id in SUPER_ADMIN_IDS:
            try:
                await message.bot.send_message( # type: ignore
                    chat_id=int(admin_id),
                    text=notification_text,
                    reply_markup=admin_keyboard,
                    parse_mode="HTML",
                )
            except Exception as e:
                logging.error(f"Failed to notify admin {admin_id} of registration: {e}")

        # If a staff member registered under a hotel, notify that hotel's Hotel Admin
        if not is_hotel_admin and user.hotel_id:
            hotel_admin = await user_repo.get_hotel_admin(user.hotel_id)
            if hotel_admin and hotel_admin.telegram_id:
                try:
                    await message.bot.send_message( # type: ignore
                        chat_id=hotel_admin.telegram_id,
                        text=(
                            f"👥 <b>New Staff Registration for {hotel_clean}</b>\n\n"
                            f"👤 <b>Name</b>: {name_clean}\n"
                            f"📱 <b>Phone</b>: {phone_clean}\n"
                            f"🆔 <b>Telegram ID</b>: <code>{message.from_user.id}</code>\n\n"
                            "<i>The administrator has been notified to activate this staff member.</i>"
                        ),
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logging.error(f"Failed to notify hotel admin of new staff: {e}")
    except Exception as e:
        logging.error(f"Failed to send registration notifications: {e}")

    await message.answer(
        "📝 Registration submitted!\n\n"
        "Your request is pending approval by the administrator.\n"
        "You will receive a notification once your account is approved.",
        parse_mode="Markdown",
    )
