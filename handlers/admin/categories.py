from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.category import Category
from database.repositories.category_repository import CategoryRepository
from database.repositories.product_repository import ProductRepository
from filters.role_filter import RoleFilter
from keyboards.admin_menu import (
    category_list_keyboard,
    category_detail_keyboard,
    confirm_delete_keyboard,
    admin_main_menu,
)
from states.admin import CategoryStates
router = Router()
router.message.filter(RoleFilter(["admin"]))
router.callback_query.filter(RoleFilter(["admin"]))

from utils.i18n import t

CATEGORIES_MENU_BTNS = ["🧺 Categories", "🗂 Categories", "🧺 ምድቦች", "🧺 Gareewwan"]

@router.message(F.text.in_(CATEGORIES_MENU_BTNS))
async def categories_menu(message: Message, session: AsyncSession, lang: str = "en"):
    repo = CategoryRepository(session)
    cats = await repo.get_all()
    await message.answer(
        t("admin_categories_title", lang, count=len(cats)),
        reply_markup=category_list_keyboard(cats, lang=lang),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "admin_categories_back")
async def categories_back(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    repo = CategoryRepository(session)
    cats = await repo.get_all()
    await callback.message.edit_text( # type: ignore
        t("admin_categories_title", lang, count=len(cats)),
        reply_markup=category_list_keyboard(cats, lang=lang),
        parse_mode="Markdown",
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_cat:"))
async def category_detail(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    cat_id = int(callback.data.split(":")[1]) # type: ignore
    repo = CategoryRepository(session)
    cat = await repo.get_by_id(cat_id)
    if not cat:
        await callback.answer("Category not found.", show_alert=True)
        return
    status = "✅ Active" if cat.is_active else "❌ Inactive"
    await callback.message.edit_text( # type: ignore
        f"🗂 *{cat.name}*\nStatus: {status}",
        reply_markup=category_detail_keyboard(cat, lang=lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_cat_add")
async def category_add_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🗂 Enter the *category name*:", parse_mode="Markdown") # type: ignore
    await state.set_state(CategoryStates.waiting_name)
    await callback.answer()


@router.message(CategoryStates.waiting_name)
async def category_add_save(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    name = message.text.strip() # type: ignore
    repo = CategoryRepository(session)
    existing = await repo.get_by_name(name)
    if existing:
        await message.answer(f"❌ Category *{name}* already exists.", parse_mode="Markdown")
        return
    cat = Category(name=name)
    await repo.create(cat)
    await message.answer(
        f"✅ Category *{cat.name}* created.",
        reply_markup=admin_main_menu(),
        parse_mode="Markdown",
    )

@router.callback_query(F.data.startswith("admin_cat_edit:"))
async def category_edit_start(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1]) # type: ignore
    await state.update_data(cat_id=cat_id)
    await callback.message.answer("✏️ Enter the *new category name*:", parse_mode="Markdown") # type: ignore
    await state.set_state(CategoryStates.editing_name)
    await callback.answer()


@router.message(CategoryStates.editing_name)
async def category_edit_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()
    repo = CategoryRepository(session)
    cat = await repo.get_by_id(data["cat_id"])
    if not cat:
        await message.answer("❌ Category not found.")
        return
    new_name = message.text.strip() # type: ignore
    existing = await repo.get_by_name(new_name)
    if existing and existing.id != cat.id:
        await message.answer(f"❌ Name *{new_name}* is already taken.", parse_mode="Markdown")
        return
    cat.name = new_name
    await repo.update(cat)
    await message.answer(f"✅ Category renamed to *{cat.name}*.", parse_mode="Markdown")


@router.callback_query(F.data.startswith("admin_cat_deactivate:"))
async def category_deactivate(callback: CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split(":")[1]) # type: ignore
    repo = CategoryRepository(session)
    cat = await repo.get_by_id(cat_id)
    if not cat:
        await callback.answer("Not found.", show_alert=True)
        return
    await repo.soft_delete(cat)
    await callback.answer("🔴 Category deactivated.", show_alert=True)
    status = "✅ Active" if cat.is_active else "❌ Inactive"
    await callback.message.edit_text( # type: ignore
        f"🗂 *{cat.name}*\nStatus: {status}",
        reply_markup=category_detail_keyboard(cat),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("admin_cat_activate:"))
async def category_activate(callback: CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split(":")[1]) # type: ignore
    repo = CategoryRepository(session)
    cat = await repo.get_by_id(cat_id)
    if not cat:
        await callback.answer("Not found.", show_alert=True)
        return
    await repo.activate(cat)
    await callback.answer("🟢 Category activated.", show_alert=True)
    status = "✅ Active" if cat.is_active else "❌ Inactive"
    await callback.message.edit_text( # type: ignore
        f"🗂 *{cat.name}*\nStatus: {status}",
        reply_markup=category_detail_keyboard(cat),
        parse_mode="Markdown",
    )

@router.callback_query(F.data.startswith("admin_cat_delete:"))
async def category_delete_confirm(callback: CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split(":")[1]) # type: ignore
    repo = CategoryRepository(session)
    cat = await repo.get_by_id(cat_id)
    if not cat:
        await callback.answer("Not found.", show_alert=True)
        return
    await callback.message.edit_text( # type: ignore
        f"⚠️ Delete category *{cat.name}*?\nAll its products will also be deactivated.",
        reply_markup=confirm_delete_keyboard("cat", cat_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_cat:"))
async def category_delete_execute(callback: CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split(":")[1]) # type: ignore
    repo = CategoryRepository(session)
    cat = await repo.get_by_id(cat_id)
    if not cat:
        await callback.answer("Not found.", show_alert=True)
        return

    prod_repo = ProductRepository(session)
    products = await prod_repo.get_all_by_category(cat_id)
    for p in products:
        await prod_repo.soft_delete(p)

    await repo.soft_delete(cat)
    cats = await repo.get_all()
    await callback.message.edit_text( # type: ignore
        f"🗑 Category *{cat.name}* deleted.\n\n"
        f"🗂 *Categories* ({len(cats)} total)",
        reply_markup=category_list_keyboard(cats),
        parse_mode="Markdown",
    )
    await callback.answer("Deleted.")


@router.callback_query(F.data.startswith("cancel_delete_cat:"))
async def category_delete_cancel(callback: CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split(":")[1]) # type: ignore
    repo = CategoryRepository(session)
    cat = await repo.get_by_id(cat_id)
    if not cat:
        await callback.answer()
        return
    status = "✅ Active" if cat.is_active else "❌ Inactive"
    await callback.message.edit_text( # type: ignore
        f"🗂 *{cat.name}*\nStatus: {status}",
        reply_markup=category_detail_keyboard(cat),
        parse_mode="Markdown",
    )
    await callback.answer("Cancelled.")
