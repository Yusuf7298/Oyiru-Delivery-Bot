from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from database.models.order import OrderStatus
from database.repositories.order_repository import OrderRepository
from database.repositories.user_repository import UserRepository
from services.notification_service import notify_customer_status_update
from keyboards.delivery import (
    delivery_menu,
    assigned_order_keyboard,
    active_order_keyboard,
)
from filters.role_filter import RoleFilter
from utils.helpers import safe_edit_text_or_caption

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

@router.message(F.text.in_(["📦 Assigned Orders", "📦 Available Deliveries"]))
async def assigned_orders(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not driver:
        await message.answer("❌ You are not registered.")
        return

    repo = OrderRepository(session)
    data = await repo.get_driver_orders(driver.id)
    orders = data.get("assigned", [])
    if not orders:
        await message.answer("📭 No assigned deliveries right now.")
        return

    await message.answer(f"📦 *Assigned Deliveries* ({len(orders)})", parse_mode="Markdown")
    for order in orders:
        card = _order_card(order)
        kb = assigned_order_keyboard(order.id)
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
                        logger.warning(f"Driver order card via FSInputFile failed: {e}")
            if not sent:
                await message.answer(card, reply_markup=kb, parse_mode="Markdown")
        else:
            await message.answer(card, reply_markup=kb, parse_mode="Markdown")

@router.message(F.text.in_(["🚛 Active Delivery", "🚚 My Deliveries"]))
async def active_delivery(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not driver:
        await message.answer("❌ You are not registered.")
        return

    repo = OrderRepository(session)
    data = await repo.get_driver_orders(driver.id)
    orders = data.get("accepted", [])

    if not orders:
        await message.answer("🚦 No active deliveries in progress.")
        return

    await message.answer(f"🚛 *Active Deliveries* ({len(orders)})", parse_mode="Markdown")
    for order in orders:
        accepted_str = _fmt_time(order.accepted_at)
        text = _order_card(order) + f"\n⏱ Accepted: {accepted_str}"
        await message.answer(
            text,
            reply_markup=active_order_keyboard(order.id),
            parse_mode="Markdown",
        )

@router.message(F.text == "📜 Delivery History")
async def delivery_history(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not driver:
        await message.answer("❌ You are not registered.")
        return

    repo = OrderRepository(session)
    data = await repo.get_driver_orders(driver.id)
    orders = data.get("completed", [])

    if not orders:
        await message.answer("📭 No completed deliveries yet.")
        return

    lines = [f"📜 Delivery History ({len(orders)})\n"]
    for order in orders:
        lines.append(
            f"• `{order.order_number}` — {order.hotel.name if order.hotel else '—'}\n"
            f"  ✅ Delivered: {_fmt_time(order.delivered_at)}\n"
            f"  ⏱ Accepted:  {_fmt_time(order.accepted_at)}\n"
        )
    await message.answer("\n".join(lines), parse_mode="Markdown")

@router.message(F.text == "👤 My Profile")
async def driver_profile(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not driver:
        await message.answer("❌ Profile not found.")
        return

    await message.answer(
        "👤 Driver Profile\n\n"
        f"📛 Name: {driver.full_name}\n"
        f"📞 Phone: {driver.phone or '—'}\n"
        f"🆔 Telegram ID: `{driver.telegram_id}`\n"
        f"📌 Status: {'✅ Active' if driver.is_active else '❌ Inactive'}",
        parse_mode="Markdown",
    )

@router.callback_query(F.data.startswith("drv_accept:"))
async def driver_accept(callback: CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not driver:
        await callback.answer("Driver not found.", show_alert=True)
        return

    repo = OrderRepository(session)
    order, code = await repo.driver_accept(order_id, driver.id) # type: ignore
    if code == "not_found":
        await callback.answer("Order not found.", show_alert=True)
        return
    if code == "not_assigned":
        await callback.answer("⚠️ This order is not assigned to you.", show_alert=True)
        return
    if code == "wrong_status":
        await callback.answer(
            f"⚠️ Cannot accept — order is {order.status.value}.",
            show_alert=True,
        )
        return

    await callback.answer("Accepted! 🚛")

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
        reply_markup=active_order_keyboard(order.id),
        parse_mode="Markdown",
    )

@router.callback_query(F.data.startswith("drv_complete:"))
async def driver_complete(callback: CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    user_repo = UserRepository(session)
    driver = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not driver:
        await callback.answer("Driver not found.", show_alert=True)
        return

    repo = OrderRepository(session)
    order, code = await repo.driver_complete(order_id, driver.id) # type: ignore
    if code == "not_found":
        await callback.answer("Order not found.", show_alert=True)
        return
    if code == "not_assigned":
        await callback.answer("⚠️ This order is not assigned to you.", show_alert=True)
        return
    if code == "wrong_status":
        await callback.answer(
            f"⚠️ Cannot complete — order is {order.status.value}.",
            show_alert=True,
        )
        return

    await callback.answer("Delivered! ✅")

    if order.customer:
        try:
            await notify_customer_status_update(callback.bot, order, order.customer.telegram_id) # type: ignore
        except Exception as e:
            logger.error(f"Customer notify failed: {e}")

    logger.info(f"Driver {driver.full_name} ({driver.telegram_id}) completed {order.order_number}")

    await safe_edit_text_or_caption(
        callback,
        f"🎉 Delivery Completed!\n\n"
        f"{_order_card(order)}\n\n"
        f"⏱ Accepted:  {_fmt_time(order.accepted_at)}\n"
        f"✅ Delivered: {_fmt_time(order.delivered_at)}",
        parse_mode="Markdown",
    )
