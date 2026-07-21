from aiogram.utils.keyboard import ReplyKeyboardBuilder
def delivery_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📦 Available Deliveries")
    builder.button(text="🚚 My Deliveries")
    builder.button(text="📜 Delivery History")
    builder.button(text="👤 My Profile")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)