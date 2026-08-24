import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from database.models.order import OrderStatus
from database.repositories.order_repository import OrderRepository
from database.repositories.user_repository import UserRepository
from services.notification_service import (
    notify_customer_status_update,
    notify_customer_rejected,
    notify_sales_managers,
)
from states.store_manager import StoreManagerState
from keyboards.store_manager import (
    store_manager_menu,
    order_action_keyboard,
    order_detail_keyboard,
)
from filters.role_filter import RoleFilter

router = Router()
router.message.filter(RoleFilter(["hotel"]))
router.callback_query.filter(RoleFilter(["hotel"]))

def _order_summary(order) -> str:
    lines = []
    if order.file_path:
        fname = getattr(order, "original_filename", None) or "uploaded file"
        ftype = (order.file_type or "document").title()
        lines.append(f"📎 {ftype}: `{fname}`")
    else:
        for item in order.items:
            unit = item.product.unit if item.product else "KG"
            lines.append(f"• {item.product.name if item.product else '—'} — {item.quantity} {unit}")

    products_block = "\n".join(lines) or "—"
    driver_line = f"\n🚗 Driver: {order.driver_name}" if order.driver_name else ""
    partner_line = ""
    if order.delivery_partner_id:
        partner_line = f"\n👤 Delivery Partner assigned"

    return (
        f"🆔 {order.order_number}\n"
        f"🏨 Hotel: {order.hotel.name if order.hotel else '—'}\n"
        f"👤 Customer: {order.customer.full_name if order.customer else '—'}\n"
        f"📌 Status: {order.status.value}{driver_line}{partner_line}\n"
        f"📝 Note: {order.note or '—'}\n\n"
        f"🛒 Products / File:\n{products_block}"
    )


async def _send_order_card(message: Message, order, reply_markup=None):
    summary = _order_summary(order)
    if not (order.file_path or order.telegram_file_id):
        await message.answer(summary, reply_markup=reply_markup, parse_mode="Markdown")
        return

    is_photo = (order.file_type == "photo")
    if order.telegram_file_id:
        try:
            if is_photo:
                await message.answer_photo(photo=order.telegram_file_id, caption=summary, reply_markup=reply_markup, parse_mode="Markdown")
                return
            else:
                await message.answer_document(document=order.telegram_file_id, caption=summary, reply_markup=reply_markup, parse_mode="Markdown")
                return
        except Exception as e:
            logger.warning(f"Failed to send order media via telegram_file_id to store manager: {e}")

    if order.file_path:
        full_path = os.path.join(os.getcwd(), order.file_path) if not os.path.isabs(order.file_path) else order.file_path
        if os.path.exists(full_path):
            file_input = FSInputFile(full_path)
            try:
                if is_photo:
                    await message.answer_photo(photo=file_input, caption=summary, reply_markup=reply_markup, parse_mode="Markdown")
                    return
                else:
                    await message.answer_document(document=file_input, caption=summary, reply_markup=reply_markup, parse_mode="Markdown")
                    return
            except Exception as e:
                logger.warning(f"Failed to send order media via FSInputFile to store manager: {e}")

    await message.answer(summary, reply_markup=reply_markup, parse_mode="Markdown")


@router.message(F.text == "📋 Store Manager")
async def store_manager_home(message: Message):
    await message.answer(
        "🏪 *Store Manager Panel*\n\nChoose an option:",
        reply_markup=store_manager_menu(),
        parse_mode="Markdown",
    )

@router.message(F.text == "📥 New Orders")
async def new_orders(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    sm = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not sm or not sm.hotel_id:
        await message.answer("❌ You are not assigned to a hotel.")
        return
    repo = OrderRepository(session)
    orders = await repo.get_new_orders(sm.hotel_id)
    if not orders:
        await message.answer("✅ No new orders pending review.")
        return
    for order in orders:
        await _send_order_card(
            message,
            order,
            reply_markup=order_action_keyboard(order.id, order.status, has_file=bool(order.file_path)),
        )

@router.message(F.text == "📦 Active Orders")
async def active_orders(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    sm = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not sm or not sm.hotel_id:
        await message.answer("❌ You are not assigned to a hotel.")
        return
    repo = OrderRepository(session)
    orders = await repo.get_active_orders(sm.hotel_id)
    if not orders:
        await message.answer("No active orders right now.")
        return
    for order in orders:
        await _send_order_card(
            message,
            order,
            reply_markup=order_detail_keyboard(order),
        )


@router.message(F.text == "📜 Order History")
async def order_history(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    sm = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not sm or not sm.hotel_id:
        await message.answer("❌ You are not assigned to a hotel.")
        return
    repo = OrderRepository(session)
    orders = await repo.get_order_history(sm.hotel_id)
    if not orders:
        await message.answer("No completed orders yet.")
        return
    for order in orders:
        await _send_order_card(message, order)

@router.callback_query(F.data.startswith("sm_approve:"))
async def approve_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)

    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return
    if order.status != OrderStatus.SUBMITTED:
        await callback.answer(
            f"⚠️ This order is already {order.status.value} and cannot be approved.",
            show_alert=True,
        )
        return

    await state.update_data(approving_order_id=order_id)
    await state.set_state(StoreManagerState.waiting_for_driver_name)
    await callback.message.answer( # type: ignore
        f"✅ Approving order {order.order_number}\n\n"
        "Enter the internal driver name for this delivery:",
        parse_mode="Markdown",
    )
    await callback.answer()

@router.message(StoreManagerState.waiting_for_driver_name)
async def approve_driver_name(message: Message, state: FSMContext, session: AsyncSession):
    driver_name = message.text.strip() # type: ignore
    if not driver_name:
        await message.answer("❌ Driver name cannot be empty. Please enter the driver's name:")
        return

    data = await state.get_data()
    order_id = data.get("approving_order_id")
    await state.clear()

    repo = OrderRepository(session)
    order, reason = await repo.approve_order(order_id, driver_name) # type: ignore

    if reason == "not_found":
        await message.answer("❌ Order not found.")
        return
    if reason == "already_processed":
        await message.answer(f"⚠️ Order is already {order.status.value}. No changes made.") # type: ignore
        return
    if order.customer: # type: ignore
        try:
            await notify_customer_status_update(message.bot, order, order.customer.telegram_id) # type: ignore
        except Exception as e:
            logger.error(f"Failed to notify customer: {e}")

    # Notify sales managers
    try:
        await notify_sales_managers(message.bot, order, "Approved") # type: ignore
    except Exception as e:
        logger.error(f"Failed to notify sales managers: {e}")

    await message.answer(
        f"✅ Order {order.order_number} approved.\n" # type: ignore
        f"🚗 Driver: {order.driver_name}", # type: ignore
        reply_markup=order_detail_keyboard(order),
        parse_mode="Markdown",
    )

@router.callback_query(F.data.startswith("sm_reject:"))
async def reject_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return
    if order.status != OrderStatus.SUBMITTED:
        await callback.answer(
            f"⚠️ This order is already {order.status.value} and cannot be rejected.",
            show_alert=True,
        )
        return

    await state.update_data(rejecting_order_id=order_id)
    await state.set_state(StoreManagerState.waiting_for_reject_reason)
    await callback.message.answer( # type: ignore
        f"❌ Rejecting order {order.order_number}*\n\n"
        "Enter the reason for rejection (mandatory):",
        parse_mode="Markdown",
    )
    await callback.answer()

@router.message(StoreManagerState.waiting_for_reject_reason)
async def reject_reason(message: Message, state: FSMContext, session: AsyncSession):
    reason = message.text.strip() # type: ignore
    if not reason:
        await message.answer("❌ Reason cannot be empty. Please enter the rejection reason:")
        return

    data = await state.get_data()
    order_id = data.get("rejecting_order_id")
    await state.clear()

    repo = OrderRepository(session)
    order, result = await repo.reject_order(order_id, reason) # type: ignore
    if result == "not_found":
        await message.answer("❌ Order not found.")
        return
    if result == "already_processed":
        await message.answer(f"⚠️ Order is already {order.status.value}. No changes made.") # type: ignore
        return

    if order.customer: # type: ignore
        try:
            await notify_customer_rejected(
                message.bot, order, order.customer.telegram_id, reason # type: ignore
            )
        except Exception as e:
            logger.error(f"Failed to notify customer of rejection: {e}")

    await message.answer(
        f"✅ Order *{order.order_number}* rejected.\n" # type: ignore
        f"Reason: {reason}",
        parse_mode="Markdown",
    )

_NEXT_STATUS = {
    OrderStatus.APPROVED:         OrderStatus.PREPARING,
    OrderStatus.PREPARING:        OrderStatus.PACKED,
    OrderStatus.PACKED:           OrderStatus.OUT_FOR_DELIVERY,
    OrderStatus.OUT_FOR_DELIVERY: OrderStatus.DELIVERED,
}

@router.callback_query(F.data.startswith("sm_status:"))
async def update_status(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":") # type: ignore
    order_id = int(parts[1])
    new_status_name = parts[2]

    try:
        new_status = OrderStatus[new_status_name]
    except KeyError:
        await callback.answer("Invalid status.", show_alert=True)
        return

    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return
    if new_status != OrderStatus.CANCELLED:
        allowed_next = _NEXT_STATUS.get(order.status)
        if allowed_next != new_status:
            await callback.answer(
                f"⚠️ Cannot move from {order.status.value} to {new_status.value}.",
                show_alert=True,
            )
            return

    order = await repo.update_order_status(order_id, new_status)

    # Notify customer
    if order and order.customer:
        try:
            await notify_customer_status_update(callback.bot, order, order.customer.telegram_id) # type: ignore
        except Exception as e:
            logger.error(f"Customer notification failed: {e}")

    # Notify sales managers on Delivered
    if order and new_status == OrderStatus.DELIVERED:
        try:
            await notify_sales_managers(callback.bot, order, "Delivered") # type: ignore
        except Exception as e:
            logger.error(f"Sales manager notification failed: {e}")

    from utils.helpers import safe_edit_text_or_caption
    await safe_edit_text_or_caption(
        callback,
        _order_summary(order),
        reply_markup=order_detail_keyboard(order),
        parse_mode="Markdown",
    )
    await callback.answer(f"✅ Status → {new_status.value}")


@router.callback_query(F.data.startswith("sm_message:"))
async def message_customer_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order or not order.customer:
        await callback.answer("Customer not found.", show_alert=True)
        return

    await state.update_data(message_order_id=order_id, message_customer_tid=order.customer.telegram_id)
    await state.set_state(StoreManagerState.waiting_for_message_text)
    await callback.message.answer( # type: ignore
        f"💬 Send a message to {order.customer.full_name} (Order: {order.order_number}):\n\n"
        "Type your message below:",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(StoreManagerState.waiting_for_message_text)
async def message_customer_send(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    customer_tid = data.get("message_customer_tid")
    order_id = data.get("message_order_id")

    if not customer_tid:
        await message.answer("❌ Could not find customer.")
        return

    try:
        await message.bot.send_message( # type: ignore
            chat_id=customer_tid,
            text=(
                f"📢 *Message from Oyirubot Store Manager*\n\n"
                f"{message.text}"
            ),
            parse_mode="Markdown",
        )
        await message.answer("✅ Message sent to customer.")
    except Exception as e:
        logger.error(f"Failed to send message to customer {customer_tid}: {e}")
        await message.answer(f"❌ Could not send message. Error: {e}")

@router.callback_query(F.data.startswith("hotel_view_file:"))
async def view_file(callback: CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order or not order.file_path:
        await callback.answer("File not found.", show_alert=True)
        return

    full_path = os.path.join(os.getcwd(), order.file_path)
    if not os.path.exists(full_path):
        await callback.answer("File not found on disk.", show_alert=True)
        return

    await callback.answer("Sending file…")
    file_input = FSInputFile(full_path)
    caption = f"📄 {order.original_filename or 'Document'} — Order: {order.order_number}"
    await callback.message.reply_document(file_input, caption=caption) # type: ignore
