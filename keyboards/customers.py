from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.i18n import t

def customer_menu(lang: str = "en"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_place_order", lang))],
            [KeyboardButton(text=t("btn_my_orders", lang)), KeyboardButton(text=t("btn_export_orders", lang))],
            [KeyboardButton(text=t("btn_language", lang)), KeyboardButton(text=t("btn_profile", lang))],
            [KeyboardButton(text=t("btn_help", lang))],
        ],
        resize_keyboard=True,
    )

def customer_reorder_menu(lang: str = "en"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_reorder_last", lang))],
            [KeyboardButton(text=t("btn_place_order", lang))],
            [KeyboardButton(text=t("btn_my_orders", lang)), KeyboardButton(text=t("btn_export_orders", lang))],
            [KeyboardButton(text=t("btn_language", lang)), KeyboardButton(text=t("btn_profile", lang))],
            [KeyboardButton(text=t("btn_help", lang))],
        ],
        resize_keyboard=True,
    )

def categories_keyboard(categories, selected=None, lang: str = "en"):
    if selected is None:
        selected = []
    builder = InlineKeyboardBuilder()
    for category in categories:
        icon = "✅" if category.id in selected else "⚪"
        builder.button(text=f"{icon} {category.name}", callback_data=f"cat_{category.id}")
    builder.button(text="➡️ Continue", callback_data="continue_categories")
    builder.adjust(2)
    return builder.as_markup()

def order_summary_keyboard(lang: str = "en"):
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_checkout", lang), callback_data="submit_order")
    builder.button(text=t("btn_cancel", lang), callback_data="cancel_order")
    builder.adjust(1)
    return builder.as_markup()

