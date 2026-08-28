from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, ContentType
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from database.models.order import OrderStatus
from database.repositories.order_repository import OrderRepository
from database.repositories.user_repository import UserRepository
from services.notification_service import notify_customer_status_update, notify_sales_delivery_completed
from keyboards.delivery import (
    delivery_menu,
    assigned_order_keyboard,
    active_order_keyboard,
    delivery_proof_keyboard,
)
from states.order import OrderState
from filters.role_filter import RoleFilter
from utils.helpers import safe_edit_text_or_caption
from utils.i18n import t
from utils.excel_export import generate_driver_excel

router = Router()
router.message.filter(RoleFilter(["delivery"]))
router.callback_query.filter(RoleFilter(["delivery"]))

def _fmt_time(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "—"

def _order_card(order) -> str:
    return (
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {order.hotel.name if order.hotel else '—'}\n"
        f"📍 Address: {order.hotel.address if order.hotel else '—'}\n"
        f"👤 Customer: {order.customer.full_name if order.customer else '—'}\n"
        f"📞 Phone: {order.customer.phone if order.customer else '—'}\n"
        f"📌 Status: {order.status.value}"
    )

DELIVERY_AVAILABLE_BTNS = ["📦 Assigned Orders", "📦 Available Deliveries", "📦 ያሉ ማድረሻዎች", "📦 Geessituuwwan Argaman"]
DELIVERY_ACTIVE_BTNS = ["🚛 Active Delivery", "🚚 My Deliveries", "🚚 የኔ ማድረሻዎች", "🚚 Geessituuwwan Koo"]
DELIVERY_HISTORY_BTNS = ["📜 Delivery History", "📜 የማድረሻ ታሪክ", "📜 Seenaa Geessisuu"]
PROFILE_BTNS = ["👤 Profile", "👤 My Profile", "👤 መገለጫ", "👤 Profaayilii Koo"]

from utils.i18n import t

@router.message(F.text.in_(DELIVERY_AVAILABLE_BTNS))
async def assigned_orders(message: Message, session: AsyncSession, lang: str = "en"):
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not driver:
        await message.answer("❌ You are not registered.")
        return

    repo = OrderRepository(session)
    data = await repo.get_driver_orders(driver.id)
    orders = data.get("assigned", [])
    if not orders:
        await message.answer(t("no_assigned_deliveries", lang))
        return

    await message.answer(t("assigned_deliveries_title", lang, count=len(orders)), parse_mode="Markdown")
    for order in orders:
        card = _order_card(order)
        kb = assigned_order_keyboard(order.id, lang=lang)
        # If order was placed via photo/file upload, send the file so driver can see it
        if order.telegram_file_id or order.file_path:
            sent = False
            if order.telegram_file_id:
                try:
                    if order.file_type == "photo":
                        await message.answer_photo(photo=order.telegram_file_id, caption=card, reply_markup=kb, parse_mode="Markdown")
                    else:
                        await message.answer_document(document=order.telegram_file_id, caption=card, reply_markup=kb, parse_mode="Markdown")
                    sent = True
                except Exception as e:
                    try:
                        if order.file_type == "photo":
                            await message.answer_photo(photo=order.telegram_file_id, caption=card, reply_markup=kb)
                        else:
                            await message.answer_document(document=order.telegram_file_id, caption=card, reply_markup=kb)
                        sent = True
                    except Exception:
                        logger.warning(f"Driver order card via file_id failed: {e}")
            if not sent and order.file_path:
                import os
                from aiogram.types import FSInputFile
                full_path = os.path.join(os.getcwd(), order.file_path) if not os.path.isabs(order.file_path) else order.file_path
                if os.path.exists(full_path):
                    try:
                        f = FSInputFile(full_path)
                        if order.file_type == "photo":
                            await message.answer_photo(photo=f, caption=card, reply_markup=kb, parse_mode="Markdown")
                        else:
                            await message.answer_document(document=f, caption=card, reply_markup=kb, parse_mode="Markdown")
                        sent = True
                    except Exception as e:
                        try:
                            f = FSInputFile(full_path)
                            if order.file_type == "photo":
                                await message.answer_photo(photo=f, caption=card, reply_markup=kb)
                            else:
                                await message.answer_document(document=f, caption=card, reply_markup=kb)
                            sent = True
                        except Exception:
                            logger.warning(f"Driver order card via FSInputFile failed: {e}")
            if not sent:
                try:
                    await message.answer(card, reply_markup=kb, parse_mode="Markdown")
                except Exception:
                    await message.answer(card, reply_markup=kb)
        else:
            await message.answer(card, reply_markup=kb, parse_mode="Markdown")

@router.message(F.text.in_(DELIVERY_ACTIVE_BTNS))
async def active_delivery(message: Message, session: AsyncSession, lang: str = "en"):
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not driver:
        await message.answer("❌ You are not registered.")
        return

    repo = OrderRepository(session)
    data = await repo.get_driver_orders(driver.id)
    orders = data.get("accepted", [])

    if not orders:
        await message.answer(t("no_active_deliveries", lang))
        return

    await message.answer(t("active_deliveries_title", lang, count=len(orders)), parse_mode="Markdown")
    for order in orders:
        accepted_str = _fmt_time(order.accepted_at)
        text = _order_card(order) + f"\n⏱ Accepted: {accepted_str}"
        kb = active_order_keyboard(order.id, lang=lang)
        if order.telegram_file_id or order.file_path:
            sent = False
            if order.telegram_file_id:
                try:
                    if order.file_type == "photo":
                        await message.answer_photo(photo=order.telegram_file_id, caption=text, reply_markup=kb, parse_mode="Markdown")
                    else:
                        await message.answer_document(document=order.telegram_file_id, caption=text, reply_markup=kb, parse_mode="Markdown")
                    sent = True
                except Exception as e:
                    logger.warning(f"Driver active card via file_id failed: {e}")
            if not sent and order.file_path:
                import os
                from aiogram.types import FSInputFile
                full_path = os.path.join(os.getcwd(), order.file_path) if not os.path.isabs(order.file_path) else order.file_path
                if os.path.exists(full_path):
                    try:
                        f = FSInputFile(full_path)
                        if order.file_type == "photo":
                            await message.answer_photo(photo=f, caption=text, reply_markup=kb, parse_mode="Markdown")
                        else:
                            await message.answer_document(document=f, caption=text, reply_markup=kb, parse_mode="Markdown")
                        sent = True
                    except Exception as e:
                        logger.warning(f"Driver active card via FSInputFile failed: {e}")
            if not sent:
                await message.answer(text, reply_markup=kb, parse_mode="Markdown")
        else:
            await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.message(F.text.in_(DELIVERY_HISTORY_BTNS))
async def delivery_history(message: Message, session: AsyncSession, lang: str = "en"):
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not driver:
        await message.answer("❌ You are not registered.")
        return

    repo = OrderRepository(session)
    data = await repo.get_driver_orders(driver.id)
    orders = data.get("completed", [])

    if not orders:
        await message.answer(t("no_delivery_history", lang))
        return

    lines = [f"{t('delivery_history_title', lang, count=len(orders))}\n"]
    for order in orders:
        lines.append(
            f"• `{order.order_number}` — {order.hotel.name if order.hotel else '—'}\n"
            f"  ✅ Delivered: {_fmt_time(order.delivered_at)}\n"
            f"  ⏱ Accepted:  {_fmt_time(order.accepted_at)}\n"
        )
    await message.answer("\n".join(lines), parse_mode="Markdown")

@router.message(F.text.in_(PROFILE_BTNS))
async def driver_profile(message: Message, session: AsyncSession, lang: str = "en"):
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not driver:
        await message.answer("❌ Profile not found.")
        return

    text = (
        f"{t('driver_profile_title', lang)}\n\n"
        f"📛 Name: {driver.full_name}\n"
        f"📞 Phone: {driver.phone or '—'}\n"
        f"🆔 Telegram ID: `{driver.telegram_id}`\n"
        f"📌 Status: {'✅ Active' if driver.is_active else '❌ Inactive'}"
    )
    try:
        await message.answer(text, parse_mode="Markdown")
    except Exception:
        await message.answer(text)

@router.callback_query(F.data.startswith("drv_accept:"))
async def driver_accept(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not driver:
        try:
            await callback.answer("Driver not found.", show_alert=True)
        except Exception:
            pass
        return

    repo = OrderRepository(session)
    order, code = await repo.driver_accept(order_id, driver.id) # type: ignore
    if code == "not_found":
        try:
            await callback.answer("Order not found.", show_alert=True)
        except Exception:
            pass
        return
    if code == "not_assigned":
        try:
            await callback.answer("⚠️ This order is not assigned to you.", show_alert=True)
        except Exception:
            pass
        return
    if code == "wrong_status":
        try:
            await callback.answer(
                f"⚠️ Cannot accept — order is {order.status.value}.",
                show_alert=True,
            )
        except Exception:
            pass
        return

    try:
        await callback.answer("Accepted! 🚛")
    except Exception:
        pass

    if order.customer:
        try:
            await notify_customer_status_update(callback.bot, order, order.customer.telegram_id) # type: ignore
        except Exception as e:
            logger.error(f"Customer notify failed: {e}")

    logger.info(f"Driver {driver.full_name} ({driver.telegram_id}) accepted {order.order_number}")

    await safe_edit_text_or_caption(
        callback,
        f"✅ Delivery Accepted\n\n"
        f"{_order_card(order)}\n\n"
        f"⏱ Accepted: {_fmt_time(order.accepted_at)}\n\n"
        "Tap *Complete Delivery* when you have delivered the order.",
        reply_markup=active_order_keyboard(order.id, lang=lang),
        parse_mode="Markdown",
    )

@router.callback_query(F.data.startswith("drv_complete:"))
async def driver_complete_prompt(callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = "en"):
    order_id = int(callback.data.split(":")[1])  # type: ignore
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not driver:
        await callback.answer("Driver not found.", show_alert=True)
        return

    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return
    if order.delivery_partner_id != driver.id:
        await callback.answer("⚠️ This order is not assigned to you.", show_alert=True)
        return

    # Build summary of items for reference
    items_summary = ""
    if order.items:
        items_summary = "\n".join(
            f"• {item.product.name if getattr(item, 'product', None) else (getattr(item, 'product_name', None) or 'Item')} — {item.quantity} {item.unit or 'KG'}"
            for item in order.items
        )
    elif order.file_path or order.telegram_file_id:
        items_summary = f"📎 Document/Uploaded Order: {order.original_filename or 'File'}"
    else:
        items_summary = "—"

    await state.update_data(
        delivery_order_id=order_id,
        delivery_driver_id=driver.id,
        delivery_items_default=items_summary,
    )
    await state.set_state(OrderState.waiting_for_delivery_proof)

    await callback.answer()
    hotel_name = order.hotel.name if order.hotel else "—"
    text = (
        f"📦 *Delivery Confirmation for Order {order.order_number}*\n\n"
        f"🏨 Hotel: *{hotel_name}*\n\n"
        f"📋 *Ordered Items Reference*:\n{items_summary}\n\n"
        "👉 *To complete delivery, please submit confirmation:*\n"
        "1️⃣ ✍️ *Type & send the delivered products list* (e.g. `Tomato 50 KG, Onion 30 KG delivered`)\n"
        "2️⃣ 📷 *Or upload a photo proof* of the delivered items or signed delivery slip\n\n"
        "_(Your confirmation will be automatically forwarded to the Sales Team)_"
    )

    await safe_edit_text_or_caption(
        callback,
        text,
        reply_markup=delivery_proof_keyboard(order.id, lang=lang),
        parse_mode="Markdown",
    )


@router.message(OrderState.waiting_for_delivery_proof, F.photo)
async def driver_delivery_photo_received(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
    photo_file_id = message.photo[-1].file_id
    caption = message.caption.strip() if message.caption else None
    data = await state.get_data()
    delivered_items = caption or data.get("delivery_items_default") or "Photo proof of delivery submitted."
    await _finish_driver_delivery(
        message_or_callback=message,
        state=state,
        session=session,
        delivered_items=delivered_items,
        photo_file_id=photo_file_id,
        driver_notes=caption or "Delivered with photo proof",
        lang=lang,
    )


@router.message(OrderState.waiting_for_delivery_proof, F.text)
async def driver_delivery_text_received(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
    text_notes = message.text.strip()
    if not text_notes:
        await message.answer("❌ Please write the delivered products list or send a photo proof:")
        return
    await _finish_driver_delivery(
        message_or_callback=message,
        state=state,
        session=session,
        delivered_items=text_notes,
        photo_file_id=None,
        driver_notes=text_notes,
        lang=lang,
    )


@router.callback_query(F.data.startswith("drv_cancel_complete:"))
async def driver_cancel_complete(callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = "en"):
    await state.clear()
    order_id = int(callback.data.split(":")[1])  # type: ignore
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    await callback.answer("Delivery completion cancelled.")
    if order:
        await safe_edit_text_or_caption(
            callback,
            f"🚛 *Active Delivery*\n\n{_order_card(order)}",
            reply_markup=active_order_keyboard(order.id, lang=lang),
            parse_mode="Markdown",
        )


async def _finish_driver_delivery(
    message_or_callback,
    state: FSMContext,
    session: AsyncSession,
    delivered_items: str = None,
    photo_file_id: str = None,
    driver_notes: str = None,
    telegram_id: int = None,
    lang: str = "en",
):
    data = await state.get_data()
    order_id = data.get("delivery_order_id")
    await state.clear()

    tid = telegram_id or (message_or_callback.from_user.id if getattr(message_or_callback, "from_user", None) else message_or_callback.chat.id)
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(tid)
    if not driver or not order_id:
        return

    repo = OrderRepository(session)
    order, code = await repo.driver_complete(order_id, driver.id)
    if code != "ok" or not order:
        err_msg = f"⚠️ Could not complete order: {code}"
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.answer(err_msg, show_alert=True)
        else:
            await message_or_callback.answer(err_msg)
        return

    # Build delivered items summary
    items_summary = delivered_items
    if not items_summary:
        if order.items:
            items_summary = "\n".join(
                f"• {item.product.name if getattr(item, 'product', None) else (getattr(item, 'product_name', None) or 'Item')} — {item.quantity} {item.unit or 'KG'}"
                for item in order.items
            )
        elif order.file_path or order.telegram_file_id:
            items_summary = f"📎 Document/Uploaded Order: {order.original_filename or 'File'}"
        else:
            items_summary = "All ordered items delivered in full."

    # Automatically forward to Sales Group & Operations
    try:
        await notify_sales_delivery_completed(
            bot=message_or_callback.bot,
            order=order,
            delivered_items_summary=items_summary,
            photo_file_id=photo_file_id,
            driver_notes=driver_notes,
        )
    except Exception as e:
        logger.error(f"Failed to forward delivery confirmation to sales group: {e}")

    # Notify customer of delivery & prompt for rating
    if order.customer:
        try:
            await notify_customer_status_update(message_or_callback.bot, order, order.customer.telegram_id)
        except Exception as e:
            logger.error(f"Customer notify failed: {e}")

    logger.info(f"Driver {driver.full_name} completed {order.order_number} and forwarded proof to sales group.")

    # Confirm to driver
    import html
    hotel_name = order.hotel.name if order.hotel else "—"
    text = (
        f"🎉 <b>Delivery Completed Successfully!</b>\n\n"
        f"🆔 <b>Order</b>: <code>{html.escape(str(order.order_number))}</code>\n"
        f"🏨 <b>Hotel</b>: {html.escape(str(hotel_name))}\n"
        f"⏱ <b>Accepted</b>: {_fmt_time(order.accepted_at)}\n"
        f"✅ <b>Delivered</b>: {_fmt_time(order.delivered_at)}\n\n"
        f"📦 <b>Delivered Products / Notes</b>:\n{html.escape(str(items_summary))}\n\n"
        f"📤 <i>Proof of delivery automatically forwarded to the Sales Team!</i>"
    )

    if isinstance(message_or_callback, CallbackQuery):
        await safe_edit_text_or_caption(message_or_callback, text, parse_mode="HTML")
    else:
        await message_or_callback.answer(text, parse_mode="HTML")

DRIVER_EXPORT_BTNS = [
    "📊 Export Deliveries (Excel)", "📊 Export Deliveries", "📊 Export Data",
    "📊 ማድረሻዎችን አውርድ (Excel)", "📊 ማድረሻዎችን አውርድ",
    "📊 Geessisuu Buusi (Excel)", "📊 Geessisuu Buusi"
]

@router.message(F.text.in_(DRIVER_EXPORT_BTNS))
async def driver_export_deliveries(message: Message, session: AsyncSession, lang: str = "en"):
    await message.answer(t("exporting_excel", lang))
    try:
        user_repo = UserRepository(session)
        driver = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
        if not driver:
            await message.answer("❌ Profile not found.")
            return

        repo = OrderRepository(session)
        data = await repo.get_driver_orders(driver.id)
        orders = data.get("completed", []) + data.get("accepted", []) + data.get("assigned", [])
        if not orders:
            await message.answer(t("no_orders_to_export", lang))
            return

        xlsx_bytes = generate_driver_excel(driver, orders)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        safe_name = "".join(c for c in (driver.full_name or "driver") if c.isalnum() or c in ('_', '-'))
        filename = f"oyirubot_deliveries_{safe_name}_{ts}.xlsx"
        doc = BufferedInputFile(xlsx_bytes, filename=filename)

        caption = (
            f"📊 *Oyirubot Delivery Partner Report*\n\n"
            f"🚚 Driver: *{driver.full_name}*\n"
            f"📦 Total Deliveries Exported: *{len(orders)}*\n"
            f"📅 Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        )
        await message.answer_document(doc, caption=caption, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Driver Excel export failed: {e}")
        await message.answer(f"❌ Export failed: {e}")

