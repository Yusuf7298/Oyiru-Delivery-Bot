from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.types import KeyboardButton

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 New Orders"), KeyboardButton(text="🚚 Assign Driver")],
            [KeyboardButton(text="📊 Statistics"), KeyboardButton(text="📊 Export Excel Report")],
        ],
        resize_keyboard=True,
    )

def assign_driver_keyboard(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚚 Assign Driver",
                    callback_data=f"assign_driver:{order_id}",
                )
            ]
        ]
    )
