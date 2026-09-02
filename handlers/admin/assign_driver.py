import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.order import OrderStatus
from database.repositories.order_repository import OrderRepository
from database.repositories.user_repository import UserRepository
from filters.role_filter import RoleFilter
from services.notification_service import (
    notify_driver_assigned,
    notify_customer_status_update,
    notify_sales_managers,
)

router = Router()
# Both admin, store manager and hotel admin can assign drivers
router.callback_query.filter(RoleFilter(["admin", "hotel", "hotel_admin", "store_manager"]))


# ── Admin path: assign_driver:<id> → driver:<id>:<driver_id> ──────────────────

@router.callback_query(F.data.startswith("assign_driver:"))
async def choose_driver(callback: CallbackQuery, session: AsyncSession) -> None:
    order_id_str = callback.data.split(":")[1] # type: ignore
    drivers = await UserRepository(session).get_delivery_partners()
    if not drivers:
        await callback.answer(
            "⚠️ No active drivers found.\n\nPlease ensure a Driver is registered and activated in 👥 Users.",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"🚗 {driver.full_name}",
                callback_data=f"driver:{order_id_str}:{driver.id}",
            )]
            for driver in drivers
        ]
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard) # type: ignore
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("driver:"))
async def assign_driver_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":") # type: ignore
    order_id  = int(parts[1])
    driver_id = int(parts[2])
    await _do_assign(callback, session, order_id, driver_id)


# ── Store Manager path: sm_assign_driver:<id> → sm_pick_driver:<id>:<driver_id> ─

from utils.i18n import t

@router.callback_query(F.data.startswith("sm_assign_driver:"))
async def sm_choose_driver(callback: CallbackQuery, session: AsyncSession, lang: str = "en") -> None:
    order_id_str = callback.data.split(":")[1] # type: ignore
    drivers = await UserRepository(session).get_delivery_partners()
    if not drivers:
        await callback.answer(
            "⚠️ No active drivers found.\n\nPlease ensure a Driver is registered and activated in 👥 Users.",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"🚗 {driver.full_name}",
                callback_data=f"sm_pick_driver:{order_id_str}:{driver.id}",
            )]
            for driver in drivers
        ] + [[InlineKeyboardButton(text=t("btn_cancel", lang), callback_data=f"sm_driver_cancel:{order_id_str}")]]
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard) # type: ignore
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("sm_pick_driver:"))
async def sm_assign_driver_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":") # type: ignore
    order_id  = int(parts[1])
    driver_id = int(parts[2])
    await _do_assign(callback, session, order_id, driver_id)


@router.callback_query(F.data.startswith("sm_driver_cancel:"))
async def sm_driver_cancel(callback: CallbackQuery, session: AsyncSession) -> None:
    order_id = int(callback.data.split(":")[1]) # type: ignore
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    from keyboards.store_manager import order_detail_keyboard
    await callback.message.edit_reply_markup( # type: ignore
        reply_markup=order_detail_keyboard(order)
    )
    await callback.answer("Driver assignment cancelled.")


# ── Shared assignment logic ───────────────────────────────────────────────────

async def _do_assign(callback: CallbackQuery, session: AsyncSession,
                     order_id: int, driver_id: int) -> None:
    order_repo = OrderRepository(session)
    user_repo  = UserRepository(session)

    order = await order_repo.get_order(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    status_val = order.status.value if hasattr(order.status, "value") else str(order.status)
    if status_val in (OrderStatus.OUT_FOR_DELIVERY.value, OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value):
        await callback.answer(
            f"Cannot assign driver — order is already {status_val}.",
            show_alert=True,
        )
        return

    driver = await user_repo.get(driver_id)
    if not driver:
        await callback.answer("Driver not found.", show_alert=True)
        return

    order, code = await order_repo.assign_driver(order_id, driver_id)
    if code == "already_assigned":
        await callback.answer("⚠️ A driver is already assigned.", show_alert=True)
        return
    if code != "ok":
        await callback.answer(f"❌ Could not assign driver ({code}).", show_alert=True)
        return

    # Update driver name explicitly
    order.driver_name = driver.full_name
    await order_repo.add(order)

    # 1. Notify assigned driver
    try:
        await notify_driver_assigned(
            callback.bot, order, driver.telegram_id, driver.full_name # type: ignore
        )
    except Exception as e:
        logging.error(f"Failed to notify driver {driver.telegram_id}: {e}")

    # 2. Notify customer that order is approved with driver assigned
    if order.customer:
        try:
            await notify_customer_status_update(callback.bot, order, order.customer.telegram_id) # type: ignore
        except Exception as e:
            logging.error(f"Failed to notify customer: {e}")

    from keyboards.order_status import order_status_keyboard
    from utils.helpers import safe_edit_text_or_caption
    
    text = (
        f"📦 *Order*: {order.order_number}\n"
        f"👤 *Customer*: {order.customer.full_name if order.customer else '—'}\n"
        f"📌 *Status*: {order.status.value if hasattr(order.status, 'value') else order.status}\n"
        f"🚗 *Driver*: {driver.full_name}\n\n"
        f"✅ *{driver.full_name}* assigned to order *{order.order_number}*."
    )
    await safe_edit_text_or_caption(
        callback,
        text,
        reply_markup=order_status_keyboard(order),
        parse_mode="Markdown"
    )
    await callback.answer("✅ Driver assigned!")
