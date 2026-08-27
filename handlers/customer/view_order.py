from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
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
from utils.i18n import t
from utils.excel_export import generate_customer_excel

router = Router()
router.message.filter(RoleFilter(["customer", "hotel"]))
router.callback_query.filter(RoleFilter(["customer", "hotel"]))

PAGE_SIZE = 5
_STATUS_ICON = {
    "Submitted":       "📩",
    "Approved":        "✅",
    "Preparing":       "👨‍🍳",
    "Packed":          "📦",
    "Out For Delivery": "🚚",
    "Delivered":       "🎉",
    "Cancelled":       "❌",
}


def _status_icon(status_value: str) -> str:
    return _STATUS_ICON.get(status_value, "📌")

def _list_keyboard(orders: list, page: int, total: int, lang: str = "en") -> object:
    builder = InlineKeyboardBuilder()
    for order in orders:
        date_str = order.created_at.strftime("%d %b %Y") if order.created_at else "—"
        hotel_name = order.hotel.name if order.hotel else "—"
        icon = _status_icon(order.status.value)
        builder.button(
            text=f"{icon} {order.order_number} · {date_str} · {hotel_name}",
            callback_data=f"hist_view:{order.id}:{page}",
        )

    nav = []
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    if page > 0:
        nav.append((t("btn_prev", lang), f"hist_page:{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        nav.append((t("btn_next", lang), f"hist_page:{page + 1}"))

    for label, cb in nav:
        builder.button(text=label, callback_data=cb)

    builder.button(text="📊 " + t("btn_export_orders", lang), callback_data="cust_export_orders")
    builder.button(text=t("btn_close", lang), callback_data="hist_close")

    row_widths = [1] * len(orders)
    if nav:
        row_widths.append(len(nav))
    row_widths.append(1)
    row_widths.append(1)

    builder.adjust(*row_widths)
    return builder.as_markup()


def _detail_keyboard(order_id: int, page: int, is_upload: bool, lang: str = "en") -> object:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_repeat_order", lang),  callback_data=f"hist_repeat:{order_id}")
    builder.button(text=t("btn_back_to_list", lang),  callback_data=f"hist_page:{page}")
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
        lines.append(f"🚚 Driver: {order.driver_name}")
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

@router.message(F.text.in_(["📦 My Orders", "📦 View Orders", "📦 የኔ ትዕዛዞች", "📦 Ajajawwan Koo"]))
async def view_orders(message: Message, session: AsyncSession, lang: str = "en"):
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(message.from_user.id)
    if not customer:
        await message.answer("❌ You are not registered.")
        return

    repo = OrderRepository(session)
    all_orders = await repo.get_customer_orders(customer.id)
    total = len(all_orders)
    if total == 0:
        await message.answer("📭 You haven't placed any orders yet.")
        return

    orders = all_orders[:PAGE_SIZE]
    await message.answer(
        f"📋 My Orders ({total} total)\n\nTap an order to see details.",
        reply_markup=_list_keyboard(orders, 0, total),
        parse_mode="Markdown",
    )

@router.callback_query(F.data.startswith("hist_page:"))
async def history_page(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    page = int(callback.data.split(":")[1])
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not customer:
        await callback.answer("Not registered.", show_alert=True)
        return

    repo = OrderRepository(session)
    all_orders = await repo.get_customer_orders(customer.id)
    total = len(all_orders)
    offset = page * PAGE_SIZE
    orders = all_orders[offset: offset + PAGE_SIZE]

    await callback.message.edit_text(
        f"📋 My Orders ({total} total)\n\nTap an order to see details.",
        reply_markup=_list_keyboard(orders, page, total, lang=lang),
        parse_mode="Markdown",
    )
    await callback.answer()

@router.callback_query(F.data.startswith("hist_view:"))
async def history_view_detail(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    parts = callback.data.split(":")
    order_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    is_upload = bool(order.file_path or order.telegram_file_id)
    from utils.helpers import safe_edit_text_or_caption
    await safe_edit_text_or_caption(
        callback,
        _order_detail_text(order),
        reply_markup=_detail_keyboard(order_id, page, is_upload, lang=lang),
        parse_mode="Markdown",
    )
    await callback.answer()

@router.callback_query(F.data.startswith("hist_repeat:"))
async def history_repeat(callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = "en"):
    order_id = int(callback.data.split(":")[1])
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    await state.clear()
    if order.file_path or order.telegram_file_id:
        await state.update_data(order_method="upload", note=order.note)
        await state.set_state(OrderState.waiting_for_document)
        await callback.message.answer(
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
        cat_index=len(selected_cat_ids),
        quantities=quantities,
        note=order.note,
    )
    await state.set_state(OrderState.reviewing_order)
    from handlers.customer.order import _send_review
    await callback.message.answer("🔄 *Repeat Order — Review*", parse_mode="Markdown")
    class _Proxy:
        from_user = callback.from_user
        chat = callback.message.chat
        async def answer(self, *args, **kwargs):
            return await callback.message.answer(*args, **kwargs)

    await _send_review(_Proxy(), state, session, lang=lang)
    await callback.answer()

@router.callback_query(F.data.startswith("hist_file:"))
async def history_download_file(callback: CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split(":")[1])
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order or not (order.file_path or order.telegram_file_id):
        await callback.answer("❌ File not found for this order.", show_alert=True)
        return

    await callback.answer("Sending file...")
    caption = f"📎 Attached file for Order {order.order_number}"
    if order.telegram_file_id:
        try:
            if order.file_type == "photo":
                await callback.message.answer_photo(photo=order.telegram_file_id, caption=caption)
            else:
                await callback.message.answer_document(document=order.telegram_file_id, caption=caption)
            return
        except Exception as e:
            logger.warning(f"hist_file via file_id failed: {e}")

    if order.file_path:
        import os
        from aiogram.types import FSInputFile
        candidate_paths = [
            os.path.join(os.getcwd(), order.file_path) if not os.path.isabs(order.file_path) else order.file_path,
            os.path.join(os.getcwd(), "uploads", os.path.basename(order.file_path)),
            order.file_path,
        ]
        valid_path = next((p for p in candidate_paths if os.path.exists(p)), None)
        if valid_path:
            f = FSInputFile(valid_path)
            if order.file_type == "photo":
                await callback.message.answer_photo(photo=f, caption=caption)
            else:
                await callback.message.answer_document(document=f, caption=caption)
            return

    await callback.message.answer("❌ Could not load the attached file from server storage.")

@router.callback_query(F.data == "hist_close")
async def history_close(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    order_repo = OrderRepository(session)
    last = await order_repo.get_last_order(customer.id) if customer else None
    menu = customer_reorder_menu(lang) if last else customer_menu(lang)
    await callback.message.delete()
    await callback.message.answer("Main menu:", reply_markup=menu)
    await callback.answer()

async def _send_customer_excel_report(target, user_id: int, session: AsyncSession, lang: str = "en"):
    try:
        user_repo = UserRepository(session)
        customer = await user_repo.get_by_telegram_id(user_id)
        if not customer:
            msg = "❌ User profile not found."
            if isinstance(target, CallbackQuery):
                await target.message.answer(msg)
            else:
                await target.answer(msg)
            return

        order_repo = OrderRepository(session)
        orders = await order_repo.get_customer_orders(customer.id)
        if not orders:
            msg = t("no_orders_to_export", lang)
            if isinstance(target, CallbackQuery):
                await target.message.answer(msg)
            else:
                await target.answer(msg)
            return

        xlsx_bytes = generate_customer_excel(customer, orders)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        safe_name = "".join(c for c in (customer.full_name or "customer") if c.isalnum() or c in ('_', '-'))
        filename = f"oyirubot_orders_{safe_name}_{ts}.xlsx"
        doc = BufferedInputFile(xlsx_bytes, filename=filename)

        caption = (
            f"📊 *Oyirubot Customer Orders Export*\n\n"
            f"👤 Customer: *{customer.full_name}*\n"
            f"🏨 Hotel: *{customer.hotel.name if customer.hotel else '—'}*\n"
            f"📦 Total Orders Exported: *{len(orders)}*\n"
            f"📅 Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        )
        if isinstance(target, CallbackQuery):
            await target.message.answer_document(doc, caption=caption, parse_mode="Markdown")
        else:
            await target.answer_document(doc, caption=caption, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Customer Excel export failed: {e}")
        err = f"❌ Export failed: {e}"
        if isinstance(target, CallbackQuery):
            await target.message.answer(err)
        else:
            await target.answer(err)

CUSTOMER_EXPORT_BTNS = [
    "📊 Export Orders (Excel)", "📊 Export Orders", "📊 Export Data",
    "📊 ትዕዛዞችን አውርድ (Excel)", "📊 ትዕዛዞችን አውርድ",
    "📊 Ajajawwan Buusi (Excel)", "📊 Ajajawwan Buusi"
]

@router.callback_query(F.data == "cust_export_orders")
async def customer_export_callback(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    await callback.answer()
    await callback.message.answer(t("exporting_excel", lang))
    await _send_customer_excel_report(callback, callback.from_user.id, session, lang)

@router.message(F.text.in_(CUSTOMER_EXPORT_BTNS))
async def customer_export_message(message: Message, session: AsyncSession, lang: str = "en"):
    await message.answer(t("exporting_excel", lang))
    await _send_customer_excel_report(message, message.from_user.id, session, lang)

