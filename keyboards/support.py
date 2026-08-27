from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.i18n import t

def support_keyboard(support: dict, lang: str = "en") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if support.get("telegram_link"):
        builder.button(text=t("btn_chat_telegram", lang), url=support["telegram_link"])
    if support.get("phone_clean"):
        builder.button(text=t("btn_call_support", lang), url=f"tel:{support['phone_clean']}")
    if support.get("email"):
        builder.button(text=t("btn_email_support", lang), url=f"mailto:{support['email']}")
    builder.adjust(1)
    return builder.as_markup()

def admin_support_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Edit Phone Number", callback_data="admin_support_edit_phone")
    builder.button(text="✉️ Edit Email Address", callback_data="admin_support_edit_email")
    builder.button(text="💬 Edit Telegram Link", callback_data="admin_support_edit_telegram")
    builder.button(text="🔄 Reset to Default", callback_data="admin_support_reset")
    builder.button(text=t("btn_back", lang), callback_data="admin_support_back")
    builder.adjust(1)
    return builder.as_markup()
