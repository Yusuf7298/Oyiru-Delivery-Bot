from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.models.order import OrderStatus


def delivery_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📦 Assigned Orders")
    builder.button(text="🚛 Active Delivery")
    builder.button(text="📜 Delivery History")
    builder.button(text="👤 My Profile")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def assigned_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Shown for APPROVED orders — driver can accept."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Accept Delivery", callback_data=f"drv_accept:{order_id}")
    builder.adjust(1)
    return builder.as_markup()


def active_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Shown for OUT_FOR_DELIVERY orders — driver can complete."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Complete Delivery", callback_data=f"drv_complete:{order_id}")
    builder.adjust(1)
    return builder.as_markup()
