from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

def products_keyboard(products):
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=product.name,
                callback_data=f"product:{product.id}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Categories",
            callback_data="back_categories",
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )
