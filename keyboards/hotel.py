from aiogram.utils.keyboard import ReplyKeyboardBuilder
def hotel_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📥 New Orders")
    kb.button(text="📦 Active Orders")
    kb.button(text="📜 Order History")
    kb.button(text="👤 Profile")
    kb.adjust(2, 2)

    return kb.as_markup(resize_keyboard=True)