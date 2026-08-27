from typing import Any
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.repositories.user_repository import UserRepository
from keyboards.language_keyboard import language_keyboard
from keyboards.customers import customer_menu
from database.models.user import UserRole
from utils.i18n import t

router = Router()

@router.message(Command("language"))
@router.message(F.text.contains("Language"))
@router.message(F.text.contains("ቋንቋ"))
@router.message(F.text.contains("Afaan"))
async def choose_language(message: Message, lang: str = "en") -> None:
    await message.answer(
        t("select_language", lang),
        reply_markup=language_keyboard()
    )

from config.settings import SUPER_ADMIN_IDS # type: ignore

@router.callback_query(F.data.startswith("set_lang:"))
async def set_language(callback: CallbackQuery, session: Any = None, state: FSMContext = None, lang: str = "en") -> None:
    new_lang = callback.data.split(":")[1]
    user = None
    is_super_admin = str(callback.from_user.id) in SUPER_ADMIN_IDS
    
    if session is not None:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if user:
            user.language = new_lang
            await user_repo.add(user)
        elif is_super_admin:
            from database.models.user import User, UserRole
            user = User(
                telegram_id=callback.from_user.id,
                full_name=callback.from_user.full_name or "Admin",
                username=callback.from_user.username,
                role=UserRole.ADMIN,
                is_active=True,
                language=new_lang,
            )
            await user_repo.add(user)
    
    if state is not None:
        await state.update_data(language=new_lang)
    
    confirm_text = t("lang_changed", new_lang)
    try:
        await callback.answer(confirm_text, show_alert=True)
    except Exception:
        pass
    
    role_val = (user.role.value if hasattr(user.role, "value") else str(user.role)) if user else ("admin" if is_super_admin else "customer")

    if is_super_admin or (user and user.is_active):
        if role_val in ("driver", "delivery"):
            from keyboards.delivery import delivery_menu
            await callback.message.answer(
                t("welcome_back", new_lang, name=user.full_name if user else "Driver"),
                reply_markup=delivery_menu(new_lang),
            )
        elif role_val in ("hotel_admin", "hotel"):
            from keyboards.store_manager import hotel_admin_menu
            await callback.message.answer(
                t("welcome_back", new_lang, name=user.full_name if user else "Hotel Admin"),
                reply_markup=hotel_admin_menu(new_lang),
            )
        elif role_val == "store_manager":
            from keyboards.store_manager import store_manager_menu
            await callback.message.answer(
                t("welcome_back", new_lang, name=user.full_name if user else "Store Manager"),
                reply_markup=store_manager_menu(new_lang),
            )
        elif role_val == "admin" or is_super_admin:
            from keyboards.admin_menu import admin_main_menu
            await callback.message.answer(
                t("welcome_admin", new_lang, name=user.full_name if user else "Admin"),
                reply_markup=admin_main_menu(new_lang),
            )
        else:
            from keyboards.customers import customer_menu
            await callback.message.answer(
                t("welcome_back", new_lang, name=user.full_name if user else "Customer"),
                reply_markup=customer_menu(new_lang),
            )
    else:
        try:
            await callback.message.edit_text(confirm_text)
        except Exception:
            await callback.message.answer(confirm_text)

