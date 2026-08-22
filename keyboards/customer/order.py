from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import t

def order_method_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_categories", lang))],
            [KeyboardButton(text=t("btn_upload_list", lang))],
            [KeyboardButton(text=t("btn_back", lang))],
        ],
        resize_keyboard=True,
    )

def category_select_keyboard(categories: list, selected_ids: list[int], lang: str = "en") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        icon = "✅" if cat.id in selected_ids else "⚪"
        builder.button(
            text=f"{icon} {cat.name}",
            callback_data=f"toggle_cat:{cat.id}",
        )
    builder.button(text=t("btn_continue", lang), callback_data="cats_done")
    builder.button(text=t("btn_cancel", lang), callback_data="order_cancel")
    builder.adjust(2)
    return builder.as_markup()

def order_review_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_submit_order", lang), callback_data="order_submit")
    builder.button(text=t("btn_edit_note", lang), callback_data="order_edit_note")
    builder.button(text=t("btn_cancel", lang), callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()

def upload_review_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_submit_order", lang), callback_data="upload_submit")
    builder.button(text=t("btn_edit_note", lang), callback_data="upload_edit_note")
    builder.button(text=t("btn_replace_file", lang), callback_data="upload_replace_file")
    builder.button(text=t("btn_cancel", lang), callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()

def skip_note_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_skip_note", lang))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

