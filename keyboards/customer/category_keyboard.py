from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def categories_keyboard(categories):
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category.name,
                callback_data=f"category:{category.id}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="back_order_methods",
        )
    ])
    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )
