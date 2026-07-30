from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models.hotel import Hotel
def hotels_keyboard(hotels: list[Hotel]):
    builder = InlineKeyboardBuilder()
    for hotel in hotels:
        builder.button(
            text=hotel.name,
            callback_data=f"hotel:{hotel.id}"
        )
    builder.adjust(1)
    return builder.as_markup()