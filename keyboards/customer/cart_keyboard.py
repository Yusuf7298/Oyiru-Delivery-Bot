from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import KeyboardButton

def continue_order_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Add More Products")
            ],
            [
                KeyboardButton(text="✅ Checkout")
            ],
            [
                KeyboardButton(text="❌ Cancel Order")
            ],
        ],
        resize_keyboard=True,
    )

