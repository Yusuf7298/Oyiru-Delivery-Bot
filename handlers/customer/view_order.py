from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from database.repositories.user_repository import UserRepository
from database.repositories.order_repository import OrderRepository
from database.repositories.product_repository import ProductRepository
from states.order import OrderState
from keyboards.customers import customer_menu, customer_reorder_menu
from filters.role_filter import RoleFilter

router = Router()
router.message.filter(RoleFilter(["customer"]))
router.callback_query.filter(RoleFilter(["customer"]))

PAGE_SIZE = 5
_STATUS_ICON = {
    "Submitted":       "📨",
    "Approved":        "✅",
    "Preparing":       "👨‍🍳",
    "Packed":          "📦",
    "Out For Delivery": "🚛",
    "Delivered":       "🎉",
    "Cancelled":       "❌",
}


def _status_icon(status_value: str) -> str:
    return _STATUS_ICON.get(status_value, "📌")

def _list_keyboard(orders: list, page: int, total: int) -> object:
    builder = InlineKeyboardBuilder()
    for order in orders:
        date_str = order.created_at.strftime("%d %b %Y") if order.created_at else "—"
        hotel_name = order.hotel.name if order.hotel else "—"
        icon = _status_icon(order.status.value)
        builder.button(
            text=f"{icon} {order.order_number}  ·  {date_str}  ·  {hotel_name}",
            callback_data=f"hist_view:{order.id}:{page}",
        )

    nav = []
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    if page > 0:
        nav.append(("⬅️ Prev", f"hist_page:{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        nav.append(("Next ➡️", f"hist_page:{page + 1}"))

    for label, cb in nav:
        builder.button(text=label, callback_data=cb)

    builder.button(text="❌ Close", callback_data="hist_close")

    row_widths = [1] * len(orders)
    if nav:
        row_widths.append(len(nav))
    row_widths.append(1)

    builder.adjust(*row_widths)
    return builder.as_markup()


def _detail_keyboard(order_id: int, page: int, is_upload: bool) -> object:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔁 Repeat Order",  callback_data=f"hist_repeat:{order_id}")
    builder.button(text="⬅️ Back to List",  callback_data=f"hist_page:{page}")
    builder.adjust(1)
    return builder.as_markup()

def _fmt_dt(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "—"


def _order_detail_text(order) -> str:
    icon = _status_icon(order.status.value)
    hotel = order.hotel.name if order.hotel else "—"
    lines = [
        f"🆔 {order.order_number}",
        f"🏨 Hotel: {hotel}",
        f"{icon} Status: {order.status.value}",
        f"📅 Placed: {_fmt_dt(order.created_at)}",
    ]

    if order.driver_name:
        lines.append(f"🚗 Driver: {order.driver_name}")
    if order.delivered_at:
        lines.append(f"✅ Delivered: {_fmt_dt(order.delivered_at)}")

    lines.append("")

    if order.file_path or order.telegram_file_id:
        ftype = (order.file_type or "document").title()
        fname = getattr(order, "original_filename", None) or "uploaded file"
        lines.append(f"📎 File: {ftype} — `{fname}`")
    elif order.items:
        lines.append("🛒 Products:")
        for item in order.items:
            unit = item.product.unit if item.product else "KG"
            name = item.product.name if item.product else "—"
            lines.append(f"  • {name} — {item.quantity} {unit}")

    if order.note:
        lines.append(f"\n📝 Note: {order.note}")

    return "\n".join(lines)

@router.message(F.text == "📋 View Orders")
async def view_orders(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not customer:
        await message.answer("❌ You are not registered.")
        return

    repo = OrderRepository(session)
    all_orders = await repo.get_customer_orders(customer.id) # type: ignore
    total = len(all_orders)
    if total == 0:
        await message.answer("📭 You haven't placed any orders yet.")
        return

    # Show first page from the full list
    orders = all_orders[:PAGE_SIZE]
    await message.answer(
        f"📋 My Orders ({total} total)\n\nTap an order to see details.",
        reply_markup=_list_keyboard(orders, 0, total), # type: ignore
        parse_mode="Markdown",
    )

@router.callback_query(F.data.startswith("hist_page:"))
async def history_page(callback: CallbackQuery, session: AsyncSession):
    page = int(callback.data.split(":")[1]) # type: ignore
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not customer:
        await callback.answer("Not registered.", show_alert=True)
        return

    repo = OrderRepository(session)
    all_orders = await repo.get_customer_orders(customer.id) # type: ignore
    total = len(all_orders)
    offset = page * PAGE_SIZE
    orders = all_orders[offset: offset + PAGE_SIZE]

    await callback.message.edit_text( # type: ignore
        f"📋 My Orders ({total} total)\n\nTap an order to see details.",
        reply_markup=_list_keyboard(orders, page, total), # type: ignore
        parse_mode="Markdown",
    )
    await callback.answer()

@router.callback_query(F.data.startswith("hist_view:"))
async def history_view_detail(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":") # type: ignore
    order_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    is_upload = bool(order.file_path or order.telegram_file_id)
    await callback.message.edit_text( # type: ignore
        _order_detail_text(order),
        reply_markup=_detail_keyboard(order_id, page, is_upload), # type: ignore
        parse_mode="Markdown",
    )
    await callback.answer()

@router.callback_query(F.data.startswith("hist_repeat:"))
async def history_repeat(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    await state.clear()
    if order.file_path or order.telegram_file_id:
        await state.update_data(order_method="upload", note=order.note)
        await state.set_state(OrderState.waiting_for_document)
        await callback.message.answer( # type: ignore
            "📄 Repeat Upload Order\n\n"
            "Please upload a new file for this order:\n"
            "  • 📷 Photo\n"
            "  • 📄 PDF\n"
            "  • 📎 Excel / Word / Text\n\n"
            "_(Previous file is not reused — please upload a fresh copy.)_",
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    if not order.items:
        await callback.answer("❌ This order has no items to repeat.", show_alert=True)
        return

    prod_repo = ProductRepository(session)
    quantities: dict = {}
    selected_cat_ids: list = []
    seen: set = set()

    for item in order.items:
        prod = await prod_repo.get_by_id(item.product_id)
        if prod and prod.is_active:
            quantities[str(prod.id)] = item.quantity
            if prod.category_id not in seen:
                selected_cat_ids.append(prod.category_id)
                seen.add(prod.category_id)

    if not quantities:
        await callback.answer(
            "⚠️ None of the original products are still active.",
            show_alert=True,
        )
        return

    await state.update_data(
        order_method="category",
        selected_cat_ids=selected_cat_ids,
        cat_index=len(selected_cat_ids),  # skip quantity loop — go straight to review
        quantities=quantities,
        note=order.note,
    )
    await state.set_state(OrderState.reviewing_order)
    from handlers.customer.order import _send_review
    await callback.message.answer("🔁 *Repeat Order — Review*", parse_mode="Markdown") # type: ignore
    class _Proxy:
        from_user = callback.from_user
        chat = callback.message.chat # type: ignore
        async def answer(self, *args, **kwargs):
            return await callback.message.answer(*args, **kwargs) # type: ignore

    await _send_review(_Proxy(), state, session) # type: ignore
    await callback.answer()

@router.callback_query(F.data == "hist_close")
async def history_close(callback: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    order_repo = OrderRepository(session)
    last = await order_repo.get_last_order(customer.id) if customer else None # type: ignore
    menu = customer_reorder_menu() if last else customer_menu()
    await callback.message.delete() # type: ignore
    await callback.message.answer("Main menu:", reply_markup=menu) # type: ignore
    await callback.answer()
