from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.user_repository import UserRepository
from filters.role_filter import RoleFilter
from keyboards.admin_menu import (
    user_section_keyboard,
    user_detail_keyboard,
    role_pick_keyboard,
    back_keyboard,
)

router = Router()
router.message.filter(RoleFilter(["admin"]))
router.callback_query.filter(RoleFilter(["admin"]))

ROLE_LABELS = {
    "customer":      "👤 Customer",
    "hotel_admin":   "🏨 Hotel Admin",
    "hotel":         "🏨 Hotel Admin",
    "store_manager": "🏪 Store Manager",
    "driver":        "🚚 Driver",
    "delivery":      "🚚 Driver",
    "admin":         "👑 Admin",
}

ROLE_SECTION_LABELS = {
    "customer":      "👤 Customers",
    "hotel_admin":   "🏨 Hotel Admins",
    "store_manager": "🏪 Store Managers",
    "driver":        "🚚 Drivers",
    "delivery":      "🚚 Drivers",
    "admin":         "👑 Admins",
    "all":           "📋 All Registered Users",
}

ROLE_SYMBOLS = {
    "customer":      "👤",
    "hotel_admin":   "🏨",
    "hotel":         "🏨",
    "store_manager": "🏪",
    "driver":        "🚚",
    "delivery":      "🚚",
    "admin":         "👑",
}


from utils.i18n import t

USERS_MENU_BTNS = ["👥 Users", "👥 ተጠቃሚዎች", "👥 Fayyadamtoota"]

@router.message(F.text.in_(USERS_MENU_BTNS))
async def users_menu(message: Message, lang: str = "en"):
    await message.answer(
        t("admin_users_title", lang),
        reply_markup=user_section_keyboard(lang=lang),
        parse_mode="Markdown",
    )


from utils.helpers import safe_edit_text_or_caption

@router.callback_query(F.data == "admin_users_back")
async def users_back(callback: CallbackQuery, lang: str = "en"):
    await safe_edit_text_or_caption(
        callback,
        t("admin_users_title", lang),
        reply_markup=user_section_keyboard(lang=lang),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_users_list:"))
async def list_users_paginated(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    parts = callback.data.split(":")  # type: ignore
    role_key = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 1

    repo = UserRepository(session)
    if role_key == "all":
        users = await repo.get_all_users()
    else:
        users = await repo.get_by_role(role_key)

    label = ROLE_SECTION_LABELS.get(role_key, "👥 Users")

    if not users:
        await safe_edit_text_or_caption(
            callback,
            f"👥 {label}\n\nNo users found in this section.",
            reply_markup=back_keyboard("admin_users_back", lang=lang),
            parse_mode=None,
        )
        await callback.answer()
        return

    PAGE_SIZE = 8
    total_users = len(users)
    total_pages = (total_users + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * PAGE_SIZE
    page_users = users[start_idx : start_idx + PAGE_SIZE]

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for u in page_users:
        status = "✅" if u.is_active else "❌"
        symbol = ROLE_SYMBOLS.get(u.role, "👤")
        builder.button(
            text=f"{status} {symbol} {u.full_name}",
            callback_data=f"admin_user_detail:{u.id}:{role_key}:{page}",
        )
    builder.adjust(1)

    # Navigation buttons row
    nav_row = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(text="◀️ Prev", callback_data=f"admin_users_list:{role_key}:{page - 1}")
        )
    nav_row.append(
        InlineKeyboardButton(text=f"Page {page}/{total_pages}", callback_data="noop")
    )
    if page < total_pages:
        nav_row.append(
            InlineKeyboardButton(text="Next ▶️", callback_data=f"admin_users_list:{role_key}:{page + 1}")
        )
    if len(nav_row) > 1:
        builder.row(*nav_row)

    if role_key in ("driver", "delivery"):
        builder.row(
            InlineKeyboardButton(text="➕ " + t("btn_add_driver", lang), callback_data="admin_driver_add"),
            InlineKeyboardButton(text="🔗 " + t("btn_driver_invite_link", lang), callback_data="admin_driver_invite"),
        )

    builder.row(
        InlineKeyboardButton(text=t("btn_back", lang), callback_data="admin_users_back")
    )

    await safe_edit_text_or_caption(
        callback,
        f"👥 *{label}* ({total_users} total)\n"
        f"✅ = Active  ❌ = Inactive\n\n"
        "Tap any user to manage their role or status:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_driver_invite")
async def driver_invite_link(callback: CallbackQuery, lang: str = "en"):
    bot_info = await callback.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=driver_join"
    text = (
        "🔗 *Driver Registration Invite Link*\n\n"
        "Share this link with delivery drivers to let them register directly:\n"
        f"`{link}`\n\n"
        "When they tap this link, they will enter their name and phone number to register."
    )
    await callback.message.answer(text, parse_mode="Markdown") # type: ignore
    await callback.answer()


from aiogram.fsm.context import FSMContext
from states.admin import DriverRegistrationStates

@router.callback_query(F.data == "admin_driver_add")
async def driver_add_start(callback: CallbackQuery, state: FSMContext, lang: str = "en"):
    await state.set_state(DriverRegistrationStates.waiting_name)
    await callback.message.answer( # type: ignore
        "🚚 *Register New Delivery Driver*\n\n"
        "Please enter the driver's *Full Name*:",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(DriverRegistrationStates.waiting_name)
async def driver_add_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("❌ Please enter a valid name (at least 2 characters):")
        return
    await state.update_data(driver_name=name)
    await state.set_state(DriverRegistrationStates.waiting_phone)
    await message.answer(
        f"📱 Enter the phone number for *{name}*:\n"
        "_(Must be a valid Ethiopian phone number, e.g. `0911223344`)_",
        parse_mode="Markdown"
    )


@router.message(DriverRegistrationStates.waiting_phone)
async def driver_add_phone(message: Message, state: FSMContext):
    raw_phone = (message.text or "").strip()
    from utils.helpers import normalize_ethiopian_phone, format_phone_display
    norm = normalize_ethiopian_phone(raw_phone)
    if not norm:
        await message.answer(
            "❌ Invalid phone number. Please enter a valid Ethiopian phone number (e.g. `0911223344` or `+251911223344`):"
        )
        return

    await state.update_data(driver_phone=format_phone_display(norm), driver_phone_norm=norm)
    await state.set_state(DriverRegistrationStates.waiting_telegram_id)
    await message.answer(
        "✈️ Enter the driver's *Telegram Username* (e.g. `@username` or send `—` to skip):",
        parse_mode="Markdown"
    )


@router.message(DriverRegistrationStates.waiting_telegram_id)
async def driver_add_username(message: Message, state: FSMContext, session: AsyncSession):
    val = (message.text or "").strip()
    username_clean = None
    if val and val != "—" and val != "-":
        username_clean = val.lstrip("@").strip()

    data = await state.get_data()
    await state.clear()

    user_repo = UserRepository(session)
    driver_name = data["driver_name"]
    formatted_phone = data["driver_phone"]
    norm_phone = data["driver_phone_norm"]

    # Check if user already exists by phone or username
    existing = await user_repo.get_by_phone(norm_phone)
    if not existing and username_clean:
        existing = await user_repo.get_by_username(username_clean)

    welcome_sent = False
    from keyboards.delivery import delivery_menu

    if existing:
        await user_repo.set_role(existing, "driver")
        await user_repo.set_active(existing, True)
        if username_clean:
            await user_repo.update_username(existing.telegram_id, username_clean)
        
        # Send direct welcome message to the existing telegram account
        if existing.telegram_id:
            try:
                user_lang = getattr(existing, "language", "en") or "en"
                uname_tag = f"@{existing.username}" if existing.username else existing.full_name
                await message.bot.send_message( # type: ignore
                    chat_id=existing.telegram_id,
                    text=(
                        f"🎉 <b>Welcome to Oyiru Delivery Team, {uname_tag}!</b>\n\n"
                        "You have been registered as an active <b>Delivery Driver</b>.\n"
                        "Use /start to open your delivery dashboard and view assigned orders."
                    ),
                    reply_markup=delivery_menu(user_lang),
                    parse_mode="HTML"
                )
                welcome_sent = True
            except Exception as e:
                logger.warning(f"Could not send welcome message to driver {existing.telegram_id}: {e}")

        welcome_note = "✅ Welcome message sent directly to driver on Telegram!" if welcome_sent else "ℹ️ Driver updated in system."
        await message.answer(
            f"🎉 *Delivery Driver Updated Successfully!*\n\n"
            f"👤 *Name*: {existing.full_name}\n"
            f"📱 *Phone*: {existing.phone or formatted_phone}\n"
            f"🏷 *Username*: @{username_clean or existing.username or '—'}\n"
            f"🔑 *Role*: 🚚 Delivery Driver\n"
            f"📌 *Status*: ✅ Active\n\n"
            f"{welcome_note}",
            parse_mode="Markdown"
        )
        return

    from database.models.user import User
    driver_user = User(
        full_name=driver_name,
        phone=formatted_phone,
        username=username_clean,
        role="driver",
        is_active=True,
    )
    await user_repo.create(driver_user)

    bot_info = await message.bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start=driver_join"
    uname_str = f"@{username_clean}" if username_clean else "—"

    await message.answer(
        f"🎉 *Delivery Driver Registered Successfully!*\n\n"
        f"👤 *Name*: {driver_name}\n"
        f"📱 *Phone*: {formatted_phone}\n"
        f"🏷 *Username*: {uname_str}\n"
        f"🔑 *Role*: 🚚 Delivery Driver\n"
        f"📌 *Status*: ✅ Active\n\n"
        f"🔗 *Invite Link for Driver*:\n`{invite_link}`\n\n"
        "When the driver opens this link in Telegram, they will instantly access their Delivery Dashboard.",
        parse_mode="Markdown"
    )


# Legacy callback compatibility handlers redirecting to admin_users_list
@router.callback_query(F.data == "admin_users_customers")
async def list_customers_legacy(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    callback.data = "admin_users_list:customer:1"
    await list_users_paginated(callback, session, lang=lang)

@router.callback_query(F.data == "admin_users_store_managers")
async def list_store_managers_legacy(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    callback.data = "admin_users_list:store_manager:1"
    await list_users_paginated(callback, session, lang=lang)

@router.callback_query(F.data == "admin_users_delivery")
async def list_delivery_legacy(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    callback.data = "admin_users_list:driver:1"
    await list_users_paginated(callback, session, lang=lang)

@router.callback_query(F.data == "admin_users_admins")
async def list_admins_legacy(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    callback.data = "admin_users_list:admin:1"
    await list_users_paginated(callback, session, lang=lang)


@router.callback_query(F.data.startswith("admin_user_detail:"))
async def user_detail(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    parts = callback.data.split(":")  # type: ignore
    user_id = int(parts[1])
    back_role = parts[2] if len(parts) > 2 else "all"
    back_page = int(parts[3]) if len(parts) > 3 else 1

    repo = UserRepository(session)
    user = await repo.get(user_id)
    if not user:
        await callback.answer("User not found.", show_alert=True)
        return
    role_label = ROLE_LABELS.get(user.role, user.role)
    status = "✅ Active" if user.is_active else "❌ Inactive"
    hotel_info = ""
    if user.hotel_id:
        from database.repositories.hotel_repository import HotelRepository
        h = await HotelRepository(session).get_by_id(user.hotel_id)
        hotel_info = f"\n🏨 Hotel: {h.name if h else '—'}"

    uname_str = f"@{user.username}" if user.username else "—"
    text = (
        f"👤 *{user.full_name}*\n\n"
        f"📱 Phone: {user.phone or '—'}\n"
        f"🏷 Username: {uname_str}\n"
        f"🆔 Telegram ID: `{user.telegram_id}`\n"
        f"🔑 Role: *{role_label}*{hotel_info}\n"
        f"📌 Status: {status}"
    )

    await safe_edit_text_or_caption(
        callback,
        text,
        reply_markup=user_detail_keyboard(user, back_role=back_role, back_page=back_page, lang=lang),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_deactivate:"))
async def user_deactivate(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    parts = callback.data.split(":")  # type: ignore
    user_id = int(parts[1])
    back_role = parts[2] if len(parts) > 2 else "all"
    back_page = int(parts[3]) if len(parts) > 3 else 1

    repo = UserRepository(session)
    user = await repo.get(user_id)
    if not user:
        await callback.answer("Not found.", show_alert=True)
        return

    await repo.set_active(user, False)
    await callback.answer("🔴 User deactivated.", show_alert=True)
    await callback.message.edit_reply_markup(  # type: ignore
        reply_markup=user_detail_keyboard(user, back_role=back_role, back_page=back_page, lang=lang)
    )


@router.callback_query(F.data.startswith("admin_user_activate:"))
async def user_activate(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    parts = callback.data.split(":")  # type: ignore
    user_id = int(parts[1])
    back_role = parts[2] if len(parts) > 2 else "all"
    back_page = int(parts[3]) if len(parts) > 3 else 1

    repo = UserRepository(session)
    user = await repo.get(user_id)
    if not user:
        await callback.answer("Not found.", show_alert=True)
        return

    await repo.set_active(user, True)
    from services.notification_service import notify_user_approved
    await notify_user_approved(callback.bot, user)
    await callback.answer("🟢 User activated.", show_alert=True)
    await callback.message.edit_reply_markup(  # type: ignore
        reply_markup=user_detail_keyboard(user, back_role=back_role, back_page=back_page, lang=lang)
    )


@router.callback_query(F.data.startswith("admin_user_change_role:"))
async def user_change_role_prompt(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    parts = callback.data.split(":")  # type: ignore
    user_id = int(parts[1])
    back_role = parts[2] if len(parts) > 2 else "all"
    back_page = int(parts[3]) if len(parts) > 3 else 1

    repo = UserRepository(session)
    user = await repo.get(user_id)
    if not user:
        await callback.answer("Not found.", show_alert=True)
        return

    current_role_label = ROLE_LABELS.get(user.role, user.role)
    await safe_edit_text_or_caption(
        callback,
        f"🔑 *Change Role for {user.full_name}*\n"
        f"Current role: *{current_role_label}*\n\n"
        "Select the new role:",
        reply_markup=role_pick_keyboard(user_id, back_role=back_role, back_page=back_page, lang=lang),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_set_role:"))
async def user_set_role(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    parts = callback.data.split(":")  # type: ignore
    user_id = int(parts[1])
    new_role = parts[2]
    back_role = parts[3] if len(parts) > 3 else "all"
    back_page = int(parts[4]) if len(parts) > 4 else 1

    repo = UserRepository(session)
    user = await repo.get(user_id)
    if not user:
        await callback.answer("Not found.", show_alert=True)
        return

    if new_role in ("hotel_admin", "hotel") and user.hotel_id:
        existing_admin = await repo.get_hotel_admin(user.hotel_id)
        if existing_admin and existing_admin.id != user.id and existing_admin.is_active:
            hotel_name = user.hotel.name if user.hotel else "this hotel"
            await callback.answer(
                f"⚠️ {hotel_name} already has a Hotel Admin ({existing_admin.full_name}). Deactivate or change that admin's role first.",
                show_alert=True
            )
            return

    await repo.set_role(user, new_role)
    role_label = ROLE_LABELS.get(new_role, new_role)
    await callback.answer(f"✅ Role updated to {role_label}", show_alert=True)

    # Notify user of the role change
    try:
        from keyboards.customers import customer_menu
        from keyboards.delivery import delivery_menu
        from keyboards.store_manager import store_manager_menu, hotel_admin_menu
        from keyboards.admin_menu import admin_main_menu
        user_lang = getattr(user, "language", "en") or "en"
        if new_role in ("driver", "delivery"):
            u_menu = delivery_menu(user_lang)
        elif new_role in ("hotel_admin", "hotel"):
            u_menu = hotel_admin_menu(user_lang)
        elif new_role == "store_manager":
            u_menu = store_manager_menu(user_lang)
        elif new_role == "admin":
            u_menu = admin_main_menu(user_lang)
        else:
            u_menu = customer_menu(user_lang)

        await callback.bot.send_message( # type: ignore
            chat_id=user.telegram_id,
            text=(
                f"🎉 <b>Account Role Updated!</b>\n\n"
                f"Your account role has been updated to: <b>{role_label}</b>.\n"
                f"Use /start to open your dashboard."
            ),
            reply_markup=u_menu,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Failed to notify user {user.telegram_id} of role update: {e}")

    # Re-render user detail card with updated role
    role_label = ROLE_LABELS.get(user.role, user.role)
    status = "✅ Active" if user.is_active else "❌ Inactive"
    hotel_info = ""
    if user.hotel_id:
        from database.repositories.hotel_repository import HotelRepository
        h = await HotelRepository(session).get_by_id(user.hotel_id)
        hotel_info = f"\n🏨 Hotel: {h.name if h else '—'}"

    text = (
        f"✅ *Role Updated Successfully!*\n\n"
        f"👤 *{user.full_name}*\n\n"
        f"📱 Phone: {user.phone or '—'}\n"
        f"🆔 Telegram ID: `{user.telegram_id}`\n"
        f"🔑 Role: *{role_label}*{hotel_info}\n"
        f"📌 Status: {status}"
    )

    await safe_edit_text_or_caption(
        callback,
        text,
        reply_markup=user_detail_keyboard(user, back_role=back_role, back_page=back_page, lang=lang),
        parse_mode="Markdown",
    )
