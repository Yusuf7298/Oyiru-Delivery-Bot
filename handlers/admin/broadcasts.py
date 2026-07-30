import asyncio
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ContentType,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database.repositories.user_repository import UserRepository
from filters.role_filter import RoleFilter
from keyboards.admin_menu import admin_main_menu

router = Router()
router.message.filter(RoleFilter(["admin"]))
router.callback_query.filter(RoleFilter(["admin"]))

_SEND_DELAY = 0.05   # seconds
class BroadcastStates(StatesGroup):
    choosing_audience = State()
    waiting_message   = State()
    confirming        = State()

AUDIENCE_OPTIONS = {
    "bc_customers":      ("👤 Customers",       ["customer"]),
    "bc_store_managers": ("🏪 Store Managers",  ["hotel"]),
    "bc_drivers":        ("🚚 Drivers",          ["delivery"]),
    "bc_everyone":       ("🌍 Everyone",         ["customer", "hotel", "delivery", "admin"]),
}


def _audience_keyboard():
    builder = InlineKeyboardBuilder()
    for cb_key, (label, _) in AUDIENCE_OPTIONS.items():
        builder.button(text=label, callback_data=cb_key)
    builder.button(text="❌ Cancel", callback_data="bc_cancel")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def _confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Send Now", callback_data="bc_confirm")
    builder.button(text="❌ Cancel",   callback_data="bc_cancel")
    builder.adjust(2)
    return builder.as_markup()


def _content_summary(data: dict) -> str:
    ctype = data.get("content_type")
    caption = data.get("caption", "")
    if ctype == "text":
        text = data.get("text", "")
        preview = text[:200] + ("…" if len(text) > 200 else "")
        return f"*Type:* Text\n\n{preview}"
    elif ctype == "photo":
        return f"*Type:* Photo 🖼\n*Caption:* {caption or '—'}"
    elif ctype == "document":
        fname = data.get("filename", "document")
        return f"*Type:* Document 📎 `{fname}`\n*Caption:* {caption or '—'}"
    elif ctype == "video":
        return f"*Type:* Video 🎬\n*Caption:* {caption or '—'}"
    return "*Type:* Unknown"


async def _send_to_user(bot, user, data: dict) -> str:
    if not user.is_active:
        return "skipped"

    ctype   = data.get("content_type")
    caption = data.get("caption") or None
    prefix  = "📢 *Message from Oyiru*\n\n"

    try:
        if ctype == "text":
            await bot.send_message(
                chat_id=user.telegram_id,
                text=prefix + data["text"],
                parse_mode="Markdown",
            )
        elif ctype == "photo":
            await bot.send_photo(
                chat_id=user.telegram_id,
                photo=data["file_id"],
                caption=(prefix + caption) if caption else prefix.strip(),
                parse_mode="Markdown",
            )
        elif ctype == "document":
            await bot.send_document(
                chat_id=user.telegram_id,
                document=data["file_id"],
                caption=(prefix + caption) if caption else prefix.strip(),
                parse_mode="Markdown",
            )
        elif ctype == "video":
            await bot.send_video(
                chat_id=user.telegram_id,
                video=data["file_id"],
                caption=(prefix + caption) if caption else prefix.strip(),
                parse_mode="Markdown",
            )
        else:
            return "skipped"
        return "sent"
    except Exception as e:
        logger.warning(f"Broadcast failed → {user.telegram_id} ({user.full_name}): {e}")
        return "failed"


@router.message(F.text == "📢 Broadcast")
async def broadcast_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📢 *Broadcast Message*\n\n"
        "Select the *audience* for this broadcast:",
        reply_markup=_audience_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(BroadcastStates.choosing_audience)


@router.callback_query(BroadcastStates.choosing_audience,
                       F.data.in_(AUDIENCE_OPTIONS.keys()))
async def audience_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    key = callback.data
    label, roles = AUDIENCE_OPTIONS[key] # type: ignore
    repo = UserRepository(session)
    recipients = await repo.get_active_by_roles(roles)
    await state.update_data(audience_key=key, audience_label=label,
                             audience_roles=roles, recipient_count=len(recipients))

    await callback.message.edit_text( # type: ignore
        f"📢 *Broadcast to: {label}*\n"
        f"👥 Recipients: *{len(recipients)} active users*\n\n"
        "Now send your message.\n"
        "Supported: *Text, Photo, Document, Video*\n"
        "_(Caption is optional for media types.)_",
        parse_mode="Markdown",
    )
    await state.set_state(BroadcastStates.waiting_message)
    await callback.answer()

@router.message(BroadcastStates.waiting_message, F.content_type == ContentType.TEXT)
async def bc_receive_text(message: Message, state: FSMContext):
    text = message.text.strip() # type: ignore
    if not text:
        await message.answer("❌ Message cannot be empty. Send your broadcast text:")
        return
    await state.update_data(content_type="text", text=text)
    await _show_preview(message, state)


@router.message(BroadcastStates.waiting_message, F.content_type == ContentType.PHOTO)
async def bc_receive_photo(message: Message, state: FSMContext):
    await state.update_data(
        content_type="photo",
        file_id=message.photo[-1].file_id, # type: ignore
        caption=message.caption or "",
    )
    await _show_preview(message, state)


@router.message(BroadcastStates.waiting_message, F.content_type == ContentType.DOCUMENT)
async def bc_receive_document(message: Message, state: FSMContext):
    await state.update_data(
        content_type="document",
        file_id=message.document.file_id, # type: ignore
        filename=message.document.file_name or "file", # type: ignore
        caption=message.caption or "",
    )
    await _show_preview(message, state)


@router.message(BroadcastStates.waiting_message, F.content_type == ContentType.VIDEO)
async def bc_receive_video(message: Message, state: FSMContext):
    await state.update_data(
        content_type="video",
        file_id=message.video.file_id, # type: ignore
        caption=message.caption or "",
    )
    await _show_preview(message, state)


@router.message(BroadcastStates.waiting_message)
async def bc_unsupported_type(message: Message):
    await message.answer(
        "❌ *Unsupported content type.*\n\n"
        "Please send one of:\n"
        "  • Text message\n"
        "  • Photo\n"
        "  • Document\n"
        "  • Video",
        parse_mode="Markdown",
    )


async def _show_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    label = data.get("audience_label", "—")
    count = data.get("recipient_count", 0)
    summary = _content_summary(data)

    await message.answer(
        f"📋 *Broadcast Preview*\n\n"
        f"👥 *Audience*: {label} ({count} users)\n\n"
        f"{summary}\n\n"
        "Confirm to send?",
        reply_markup=_confirm_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(BroadcastStates.confirming)

@router.callback_query(BroadcastStates.confirming, F.data == "bc_confirm")
async def broadcast_send(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()
    roles = data.get("audience_roles", [])
    label = data.get("audience_label", "—")
    repo = UserRepository(session)
    recipients = await repo.get_active_by_roles(roles)

    if not recipients:
        await callback.message.edit_text( # type: ignore
            "⚠️ No active users found in the selected audience. Broadcast cancelled."
        )
        await callback.answer()
        return

    # Update UI immediately
    await callback.message.edit_text( # type: ignore
        f"⏳ *Sending broadcast to {len(recipients)} users…*\n"
        "Please wait.",
        parse_mode="Markdown",
    )
    await callback.answer("Sending…")
    sent = failed = skipped = 0
    for user in recipients:
        result = await _send_to_user(callback.bot, user, data)
        if result == "sent":
            sent += 1
        elif result == "failed":
            failed += 1
        else:
            skipped += 1
        await asyncio.sleep(_SEND_DELAY)

    # Final report
    total = sent + failed + skipped
    await callback.message.edit_text( # type: ignore
        f"✅ *Broadcast Complete*\n\n"
        f"👥 *Audience*: {label}\n"
        f"📊 *Total targeted*: {total}\n\n"
        f"📤 *Sent*: {sent}\n"
        f"❌ *Failed*: {failed}\n"
        f"⏭ *Skipped* (inactive/blocked): {skipped}",
        reply_markup=None,
        parse_mode="Markdown",
    )
    logger.info(
        f"Broadcast complete — audience: {label} | "
        f"sent: {sent} | failed: {failed} | skipped: {skipped}"
    )


@router.callback_query(F.data == "bc_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast cancelled.") # type: ignore
    await callback.message.answer("Main menu:", reply_markup=admin_main_menu()) # type: ignore
    await callback.answer()
