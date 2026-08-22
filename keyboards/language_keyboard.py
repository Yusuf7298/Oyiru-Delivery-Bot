from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇬🇧 English", callback_data="set_lang:en")
    builder.button(text="🇪🇹 አማርኛ (Amharic)", callback_data="set_lang:am")
    builder.button(text="🇪🇹 Afaan Oromoo", callback_data="set_lang:om")
    builder.adjust(1)
    return builder.as_markup()

