from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

def delivery_assignment_keyboard(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="✅ Accept",
                    callback_data=f"accept_order:{order_id}",
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Reject",
                    callback_data=f"reject_order:{order_id}",
                )
            ],

        ]

    )
