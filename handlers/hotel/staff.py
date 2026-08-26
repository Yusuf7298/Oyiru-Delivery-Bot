import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.user import UserRole
from database.repositories.user_repository import UserRepository
from database.repositories.hotel_repository import HotelRepository
from database.repositories.order_repository import OrderRepository
from filters.role_filter import RoleFilter
from keyboards.store_manager import (
    staff_management_keyboard,
    staff_list_keyboard,
    staff_detail_keyboard,
)
from utils.i18n import t

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(RoleFilter(["hotel", "admin"]))
router.callback_query.filter(RoleFilter(["hotel", "admin"]))

MY_STAFF_BTNS = ["👥 My Staff", "👥 የኔ ሰራተኞች", "👥 Hojjettoota Koo"]

@router.message(F.text.in_(MY_STAFF_BTNS))
async def my_staff_menu(message: Message, session: AsyncSession, lang: str = "en") -> None:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not user or not user.hotel_id:
        await message.answer("❌ Hotel account not found.")
        return

    hotel = await HotelRepository(session).get_by_id(user.hotel_id)
    hotel_name = hotel.name if hotel else "Hotel"
    staff = await user_repo.get_hotel_staff(user.hotel_id)

    title = t("hotel_staff_mgmt_title", lang, hotel_name=hotel_name, count=len(staff))
    await message.answer(
        title,
        reply_markup=staff_management_keyboard(user.hotel_id, lang=lang),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("hotel_invite_staff:"))
async def invite_staff_callback(callback: CallbackQuery, session: AsyncSession, lang: str = "en") -> None:
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    hotel = await HotelRepository(session).get_by_id(hotel_id)
    hotel_name = hotel.name if hotel else "Hotel"

    bot_info = await callback.bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start=join_{hotel_id}"

    text = t("staff_invite_link_msg", lang, link=invite_link, hotel_name=hotel_name)
    share_url = f"https://t.me/share/url?url={invite_link}&text=Join%20{hotel_name}%20ordering%20staff%20on%20Oyirubot"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📲 Share Invite Link", url=share_url)],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data=f"hotel_staff_back:{hotel_id}")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown") # type: ignore
    await callback.answer()

@router.callback_query(F.data.startswith("hotel_staff_list:"))
async def staff_list_callback(callback: CallbackQuery, session: AsyncSession, lang: str = "en") -> None:
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    user_repo = UserRepository(session)
    staff = await user_repo.get_hotel_staff(hotel_id)

    hotel = await HotelRepository(session).get_by_id(hotel_id)
    hotel_name = hotel.name if hotel else "Hotel"

    if not staff:
        bot_info = await callback.bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start=join_{hotel_id}"
        msg = (
            f"👥 *Staff List — {hotel_name}*\n\n"
            "📭 No ordering staff members registered yet.\n"
            "Tap *🔗 Invite Staff* below to generate and share your invite link."
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t("btn_invite_staff", lang), callback_data=f"hotel_invite_staff:{hotel_id}")],
                [InlineKeyboardButton(text=t("btn_back", lang), callback_data=f"hotel_staff_back:{hotel_id}")],
            ]
        )
        await callback.message.edit_text(msg, reply_markup=kb, parse_mode="Markdown") # type: ignore
        await callback.answer()
        return

    text = f"👥 *Staff Members — {hotel_name}* ({len(staff)} total)\n\nTap a staff member to view details or change status:"
    await callback.message.edit_text( # type: ignore
        text,
        reply_markup=staff_list_keyboard(staff, hotel_id, lang=lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("hotel_staff_detail:"))
async def staff_detail_callback(callback: CallbackQuery, session: AsyncSession, lang: str = "en") -> None:
    parts = callback.data.split(":") # type: ignore
    staff_id = int(parts[1])
    hotel_id = int(parts[2])

    user_repo = UserRepository(session)
    staff_user = await user_repo.get(staff_id)
    if not staff_user:
        await callback.answer("Staff member not found.", show_alert=True)
        return

    order_repo = OrderRepository(session)
    staff_orders = await order_repo.get_customer_orders(staff_user.id)

    status_str = "✅ Active" if staff_user.is_active else "⏸️ Inactive (Deactivated)"
    reg_date = staff_user.created_at.strftime("%Y-%m-%d") if getattr(staff_user, "created_at", None) else "—"

    text = (
        f"👤 *Staff Profile*\n\n"
        f"📛 Name: *{staff_user.full_name}*\n"
        f"📞 Phone: *{staff_user.phone or '—'}*\n"
        f"🆔 Telegram ID: {staff_user.telegram_id}\n"
        f"📌 Status: *{status_str}*\n"
        f"📦 Total Orders Placed: *{len(staff_orders)}*\n"
        f"📅 Registered: *{reg_date}*"
    )
    await callback.message.edit_text( # type: ignore
        text,
        reply_markup=staff_detail_keyboard(staff_user, hotel_id, lang=lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("hotel_staff_toggle:"))
async def staff_toggle_callback(callback: CallbackQuery, session: AsyncSession, lang: str = "en") -> None:
    parts = callback.data.split(":") # type: ignore
    staff_id = int(parts[1])
    hotel_id = int(parts[2])

    user_repo = UserRepository(session)
    staff_user = await user_repo.get(staff_id)
    if not staff_user:
        await callback.answer("Staff member not found.", show_alert=True)
        return

    new_status = not staff_user.is_active
    await user_repo.set_active(staff_user, new_status)

    alert_msg = t("staff_activated", lang) if new_status else t("staff_deactivated", lang)
    await callback.answer(alert_msg, show_alert=True)

    order_repo = OrderRepository(session)
    staff_orders = await order_repo.get_customer_orders(staff_user.id)
    status_str = "✅ Active" if new_status else "⏸️ Inactive (Deactivated)"
    reg_date = staff_user.created_at.strftime("%Y-%m-%d") if getattr(staff_user, "created_at", None) else "—"

    text = (
        f"👤 *Staff Profile*\n\n"
        f"📛 Name: *{staff_user.full_name}*\n"
        f"📞 Phone: *{staff_user.phone or '—'}*\n"
        f"🆔 Telegram ID: {staff_user.telegram_id}\n"
        f"📌 Status: *{status_str}*\n"
        f"📦 Total Orders Placed: *{len(staff_orders)}*\n"
        f"📅 Registered: *{reg_date}*"
    )
    await callback.message.edit_text( # type: ignore
        text,
        reply_markup=staff_detail_keyboard(staff_user, hotel_id, lang=lang),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("hotel_staff_back:"))
async def staff_back_callback(callback: CallbackQuery, session: AsyncSession, lang: str = "en") -> None:
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    user_repo = UserRepository(session)
    hotel = await HotelRepository(session).get_by_id(hotel_id)
    hotel_name = hotel.name if hotel else "Hotel"
    staff = await user_repo.get_hotel_staff(hotel_id)

    title = t("hotel_staff_mgmt_title", lang, hotel_name=hotel_name, count=len(staff))
    await callback.message.edit_text( # type: ignore
        title,
        reply_markup=staff_management_keyboard(hotel_id, lang=lang),
        parse_mode="Markdown"
    )
    await callback.answer()
