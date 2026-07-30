from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton
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
