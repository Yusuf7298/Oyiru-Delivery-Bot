import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.settings_repository import SettingsRepository
from keyboards.support import admin_support_keyboard
from keyboards.admin_menu import admin_main_menu
from filters.role_filter import RoleFilter
from utils.i18n import t

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(RoleFilter(["admin"]))
router.callback_query.filter(RoleFilter(["admin"]))

class SupportEditStates(StatesGroup):
    waiting_phone = State()
    waiting_email = State()
    waiting_telegram = State()

ADMIN_SUPPORT_BTNS = ["📞 Support Settings", "📞 የድጋፍ መረጃ", "📞 Qunnamtii Deeggarsaa"]

def _build_admin_support_text(support: dict) -> str:
    return (
        "⚙️ *Customer Support Settings*\n\n"
        "Here is the current dynamic contact information displayed to all bot users:\n\n"
        f"📱 *Phone*: {support['phone']}\n"
        f"✉️ *Email*: {support['email']}\n"
        f"💬 *Telegram*: [@{support['telegram_username']}]({support['telegram_link']})\n\n"
        "Tap a button below to update contact details or reset to defaults:"
    )

@router.message(F.text.in_(ADMIN_SUPPORT_BTNS))
async def admin_support_dashboard(message: Message, session: AsyncSession, lang: str = "en") -> None:
    repo = SettingsRepository(session)
    support = await repo.get_support_contact()
    await message.answer(
        _build_admin_support_text(support),
        reply_markup=admin_support_keyboard(lang=lang),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "admin_support_back")
async def admin_support_back_cb(callback: CallbackQuery, lang: str = "en") -> None:
    await callback.message.delete() # type: ignore
    await callback.message.answer( # type: ignore
        t("welcome_admin", lang, name="Admin"),
        reply_markup=admin_main_menu(lang=lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_support_reset")
async def admin_support_reset_cb(callback: CallbackQuery, session: AsyncSession, lang: str = "en") -> None:
    repo = SettingsRepository(session)
    support = await repo.reset_support_contact()
    await callback.message.edit_text( # type: ignore
        _build_admin_support_text(support),
        reply_markup=admin_support_keyboard(lang=lang),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await callback.answer("✅ Support contacts reset to default!", show_alert=True)

@router.callback_query(F.data == "admin_support_edit_phone")
async def edit_phone_start(callback: CallbackQuery, state: FSMContext) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_support_cancel_edit")]])
    await callback.message.edit_text( # type: ignore
        "📱 Enter the new *Support Phone Number*\n(e.g., +251 98 438 6102):",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(SupportEditStates.waiting_phone)
    await callback.answer()

@router.message(SupportEditStates.waiting_phone)
async def edit_phone_save(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en") -> None:
    new_phone = (message.text or "").strip()
    if len(new_phone) < 4:
        await message.answer("❌ Invalid phone number. Please enter a valid number:")
        return

    await state.clear()
    repo = SettingsRepository(session)
    support = await repo.update_support_contact(phone=new_phone)
    await message.answer(
        f"✅ Support phone updated to: {support['phone']}\n\n" + _build_admin_support_text(support),
        reply_markup=admin_support_keyboard(lang=lang),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "admin_support_edit_email")
async def edit_email_start(callback: CallbackQuery, state: FSMContext) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_support_cancel_edit")]])
    await callback.message.edit_text( # type: ignore
        "✉️ Enter the new *Support Email Address*\n(e.g., oyirusupport@gmail.com):",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(SupportEditStates.waiting_email)
    await callback.answer()

@router.message(SupportEditStates.waiting_email)
async def edit_email_save(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en") -> None:
    new_email = (message.text or "").strip()
    if "@" not in new_email or "." not in new_email:
        await message.answer("❌ Invalid email format. Please enter a valid email address:")
        return

    await state.clear()
    repo = SettingsRepository(session)
    support = await repo.update_support_contact(email=new_email)
    await message.answer(
        f"✅ Support email updated to: {support['email']}\n\n" + _build_admin_support_text(support),
        reply_markup=admin_support_keyboard(lang=lang),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "admin_support_edit_telegram")
async def edit_telegram_start(callback: CallbackQuery, state: FSMContext) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_support_cancel_edit")]])
    await callback.message.edit_text( # type: ignore
        "💬 Enter the new *Telegram Username or Link*\n(e.g., @Oyrudeliveryet or https://t.me/Oyrudeliveryet):",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(SupportEditStates.waiting_telegram)
    await callback.answer()

@router.message(SupportEditStates.waiting_telegram)
async def edit_telegram_save(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en") -> None:
    new_tg = (message.text or "").strip()
    await state.clear()
    repo = SettingsRepository(session)
    support = await repo.update_support_contact(telegram=new_tg)
    await message.answer(
        f"✅ Support Telegram updated to: [@{support['telegram_username']}]({support['telegram_link']})\n\n" + _build_admin_support_text(support),
        reply_markup=admin_support_keyboard(lang=lang),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "admin_support_cancel_edit")
async def cancel_edit_cb(callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = "en") -> None:
    await state.clear()
    repo = SettingsRepository(session)
    support = await repo.get_support_contact()
    await callback.message.edit_text( # type: ignore
        _build_admin_support_text(support),
        reply_markup=admin_support_keyboard(lang=lang),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await callback.answer("Editing cancelled.")
