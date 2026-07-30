from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def order_method_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧺 Listing Order")],
            [KeyboardButton(text="📄 Upload Photo")],
            [KeyboardButton(text="⬅ Back")],
        ],
        resize_keyboard=True,
    )


def category_select_keyboard(categories: list, selected_ids: list[int]) -> InlineKeyboardMarkup:
    """Multi-select checkbox keyboard for category selection."""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        icon = "✅" if cat.id in selected_ids else "☐"
        builder.button(
            text=f"{icon} {cat.name}",
            callback_data=f"toggle_cat:{cat.id}",
        )
    builder.button(text="➡️ Continue", callback_data="cats_done")
    builder.button(text="❌ Cancel",   callback_data="order_cancel")
    builder.adjust(2)
    return builder.as_markup()


def order_review_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Submit",       callback_data="order_submit")
    builder.button(text="✏️ Edit Note",   callback_data="order_edit_note")
    builder.button(text="❌ Cancel",       callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()


def upload_review_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Submit",          callback_data="upload_submit")
    builder.button(text="✏️ Edit Note",      callback_data="upload_edit_note")
    builder.button(text="🔄 Replace File",   callback_data="upload_replace_file")
    builder.button(text="❌ Cancel",          callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()


def skip_note_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ Skip Note")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
