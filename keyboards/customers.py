from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def customer_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Place Order")],
            [KeyboardButton(text="📋 View Orders")],
            [KeyboardButton(text="🔄 Report Returned Products")],
            [KeyboardButton(text="❓ Help")],
        ],
        resize_keyboard=True,
    )


def customer_reorder_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔁 Repeat Last Order")],
            [KeyboardButton(text="🧺 New Category Order")],
            [KeyboardButton(text="📄 Upload New Product List")],
            [KeyboardButton(text="📋 View Orders")],
            [KeyboardButton(text="🔄 Report Returned Products")],
            [KeyboardButton(text="❓ Help")],
        ],
        resize_keyboard=True,
    )

def categories_keyboard(categories, selected=None):
    if selected is None:
        selected = []
    builder = InlineKeyboardBuilder()
    for category in categories:
        icon = "✅" if category.id in selected else "☑️"
        builder.button(text=f"{icon} {category.name}",callback_data=f"cat_{category.id}")
    builder.button(text="➡ Continue",callback_data="continue_categories")
    builder.adjust(2)
    return builder.as_markup()

def order_summary_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Submit Order",callback_data="submit_order")
    builder.button(text="❌ Cancel",callback_data="cancel_order")
    builder.adjust(1)
    return builder.as_markup()