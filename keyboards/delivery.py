from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from database.models.order import OrderStatus
from utils.i18n import t

def delivery_menu(lang: str = "en") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=t("available_deliveries", lang))
    builder.button(text=t("my_deliveries", lang))
    builder.button(text=t("btn_delivery_history", lang))
    builder.button(text=t("btn_export_deliveries", lang))
    builder.button(text=t("btn_profile", lang))
    builder.button(text=t("btn_language", lang))
    builder.button(text=t("btn_contact_support", lang))
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def assigned_order_keyboard(order_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_accept_delivery", lang), callback_data=f"drv_accept:{order_id}")
    builder.adjust(1)
    return builder.as_markup()

def active_order_keyboard(order_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_complete_delivery", lang), callback_data=f"drv_complete:{order_id}")
    builder.adjust(1)
    return builder.as_markup()

def delivery_proof_keyboard(order_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_cancel", lang), callback_data=f"drv_cancel_complete:{order_id}")
    builder.adjust(1)
    return builder.as_markup()

