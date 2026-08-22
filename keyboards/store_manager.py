from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models.order import OrderStatus
from utils.i18n import t

def store_manager_menu(lang: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_store_new_orders", lang)), KeyboardButton(text=t("btn_store_active_orders", lang))],
            [KeyboardButton(text=t("btn_store_order_history", lang)), KeyboardButton(text=t("btn_language", lang))],
        ],
        resize_keyboard=True,
    )

def order_action_keyboard(order_id: int, status: OrderStatus, has_file: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Approve", callback_data=f"sm_approve:{order_id}")
    builder.button(text="❌ Reject", callback_data=f"sm_reject:{order_id}")
    builder.button(text="🚚 Assign Driver", callback_data=f"sm_assign_driver:{order_id}")
    builder.button(text="💬 Message Customer", callback_data=f"sm_message:{order_id}")
    if has_file:
        builder.button(text="📄 View Document", callback_data=f"hotel_view_file:{order_id}")
    builder.adjust(2, 1, 1)
    return builder.as_markup()

def order_detail_keyboard(order) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if order.status == OrderStatus.SUBMITTED:
        builder.button(text="✅ Approve", callback_data=f"sm_approve:{order.id}")
        builder.button(text="❌ Reject", callback_data=f"sm_reject:{order.id}")

    elif order.status == OrderStatus.APPROVED:
        builder.button(text="👨‍🍳 Start Preparing", callback_data=f"sm_status:{order.id}:PREPARING")

    elif order.status == OrderStatus.PREPARING:
        builder.button(text="📦 Mark Packed", callback_data=f"sm_status:{order.id}:PACKED")

    elif order.status == OrderStatus.PACKED:
        builder.button(text="🚚 Out for Delivery", callback_data=f"sm_status:{order.id}:OUT_FOR_DELIVERY")

    elif order.status == OrderStatus.OUT_FOR_DELIVERY:
        builder.button(text="✅ Mark Delivered", callback_data=f"sm_status:{order.id}:DELIVERED")

    if order.status not in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
        builder.button(text="🚚 Assign Driver", callback_data=f"sm_assign_driver:{order.id}")

    if order.status not in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
        builder.button(text="🚫 Cancel Order", callback_data=f"sm_status:{order.id}:CANCELLED")

    builder.button(text="💬 Message Customer", callback_data=f"sm_message:{order.id}")
    
    if getattr(order, "file_path", None):
        builder.button(text="📄 View Document", callback_data=f"hotel_view_file:{order.id}")

    builder.adjust(2)
    return builder.as_markup()

def driver_pick_keyboard(drivers: list, order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in drivers:
        builder.button(
            text=f"🚚 {d.full_name}",
            callback_data=f"sm_pick_driver:{order_id}:{d.id}",
        )
    builder.button(text="❌ Cancel", callback_data=f"sm_driver_cancel:{order_id}")
    builder.adjust(1)
    return builder.as_markup()

