from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.product import Product
from database.repositories.product_repository import ProductRepository
from database.repositories.category_repository import CategoryRepository
from filters.role_filter import RoleFilter
from keyboards.admin_menu import (
    product_list_keyboard,
    product_detail_keyboard,
    category_pick_keyboard,
    confirm_delete_keyboard,
    admin_main_menu,
)
from states.admin import ProductStates

router = Router()
router.message.filter(RoleFilter(["admin"]))
router.callback_query.filter(RoleFilter(["admin"]))

from utils.i18n import t

PRODUCTS_MENU_BTNS = ["📦 Products", "📦 ምርቶች", "📦 Oomishaalee"]

@router.message(F.text.in_(PRODUCTS_MENU_BTNS))
async def products_menu(message: Message, session: AsyncSession, lang: str = "en"):
    repo = CategoryRepository(session)
    cats = await repo.get_all()
    if not cats:
        await message.answer("No categories yet. Add a category first.")
        return
    await message.answer(
        t("admin_products_title", lang),
        reply_markup=category_pick_keyboard(cats, "admin_cat_products", lang=lang),
        parse_mode="Markdown",
    )


from utils.helpers import safe_edit_text_or_caption

@router.callback_query(F.data.startswith("admin_cat_products:"))
async def products_for_category(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    cat_id = int(callback.data.split(":")[1]) # type: ignore
    cat_repo = CategoryRepository(session)
    prod_repo = ProductRepository(session)
    cat = await cat_repo.get_by_id(cat_id)
    if not cat:
        await callback.answer("Category not found.", show_alert=True)
        return
    products = await prod_repo.get_all_by_category(cat_id)
    await safe_edit_text_or_caption(
        callback,
        f"📦 *{cat.name}* — Products ({len(products)})\n\n✅ = Active  ❌ = Inactive",
        reply_markup=product_list_keyboard(products, cat_id, lang=lang),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_prod:"))
async def product_detail(callback: CallbackQuery, session: AsyncSession, lang: str = "en"):
    prod_id = int(callback.data.split(":")[1]) # type: ignore
    prod_repo = ProductRepository(session)
    prod = await prod_repo.get_by_id(prod_id)
    if not prod:
        await callback.answer("Product not found.", show_alert=True)
        return
    cat_repo = CategoryRepository(session)
    cat = await cat_repo.get_by_id(prod.category_id)
    status = "✅ Active" if prod.is_active else "❌ Inactive"
    await safe_edit_text_or_caption(
        callback,
        f"📦 *{prod.name}*\n\n"
        f"📏 Unit: {prod.unit}\n"
        f"🗂 Category: {cat.name if cat else '—'}\n"
        f"Status: {status}",
        reply_markup=product_detail_keyboard(prod, lang=lang),
        parse_mode="Markdown",
    )
    await callback.answer()


import re as _re
_BATCH_RE = _re.compile(
    r"^(.+?)\s*[-=:]\s*(.+)$"   # "Name - unit"  /  "Name = Pcs"
    r"|"
    r"^(.+?)\s+(KG|PCS|LITRE|LITER|PACK|BOX|BAG|BOTTLE|PIECE|PIECES|G|GM|ML|L|T)$",
    _re.IGNORECASE,
)


def _parse_product_line(line: str) -> tuple[str, str]:
    line = line.strip()
    if not line:
        raise ValueError("empty")

    m = _BATCH_RE.match(line)
    if m:
        if m.group(1) is not None:
            name, unit = m.group(1).strip(), m.group(2).strip()
        else:
            name, unit = m.group(3).strip(), m.group(4).strip().upper()
    else:
        # No unit found — strip any trailing numbers and default to KG
        name = _re.sub(r"\s*[-=:]?\s*\d+(\.\d+)?(\s*(kg|pcs|g|l|ml))?$", "", line, flags=_re.IGNORECASE).strip()
        unit = "KG"

    if not name:
        raise ValueError("empty name")
    unit = unit.upper() if len(unit) <= 4 else unit.capitalize()
    return name, unit


@router.callback_query(F.data.startswith("admin_prod_add:"))
async def product_add_start(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1]) # type: ignore
    await state.update_data(category_id=cat_id)
    await callback.message.answer( # type: ignore
        "📦 *Add Products*\n\n"
        "You can add *one or many products* in a single message.\n\n"
        "*Format options:*\n"
        "`Potato - KG`\n"
        "`Tomato - Pcs`\n"
        "`Sugar` _(defaults to KG)_\n\n"
        "Send multiple lines to add many at once:\n"
        "`Flour - KG\nRice - KG\nOil - Litre`",
        parse_mode="Markdown",
    )
    await state.set_state(ProductStates.waiting_batch)
    await callback.answer()


@router.message(ProductStates.waiting_batch)
async def product_add_batch(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    cat_id: int = data["category_id"]
    await state.clear()

    raw_lines = [ln.strip() for ln in message.text.splitlines() if ln.strip()] # type: ignore
    if not raw_lines:
        await message.answer("❌ Message is empty. Please try again.")
        return

    prod_repo = ProductRepository(session)
    cat_repo  = CategoryRepository(session)
    cat       = await cat_repo.get_by_id(cat_id)

    added, skipped, errors = [], [], []

    for line in raw_lines:
        try:
            name, unit = _parse_product_line(line)
        except ValueError:
            errors.append(f"❓ `{line}` — could not parse")
            continue

        existing = await prod_repo.get_by_name_in_category(name, cat_id)
        if existing:
            skipped.append(f"⚠️ *{name}* — already exists")
            continue

        product = Product(name=name, unit=unit, category_id=cat_id)
        await prod_repo.create(product)
        added.append(f"✅ *{name}* ({unit})")

    parts = []
    if added:
        parts.append("*Added:*\n" + "\n".join(added))
    if skipped:
        parts.append("*Skipped (duplicates):*\n" + "\n".join(skipped))
    if errors:
        parts.append("*Could not parse:*\n" + "\n".join(errors))

    cat_name = cat.name if cat else f"ID:{cat_id}"
    summary = (
        f"📦 *{cat_name}* — Batch Add Complete\n\n"
        + "\n\n".join(parts)
    )
    await message.answer(summary, reply_markup=admin_main_menu(), parse_mode="Markdown")


@router.message(ProductStates.waiting_name)
async def product_add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip()) # type: ignore
    await message.answer(
        "📏 Enter the *unit* (e.g. KG, Litre, Pcs) — or send — to use KG:",
        parse_mode="Markdown",
    )
    await state.set_state(ProductStates.waiting_unit)


@router.message(ProductStates.waiting_unit)
async def product_add_unit(message: Message, state: FSMContext, session: AsyncSession):
    val = message.text.strip() # type: ignore
    unit = "KG" if val == "—" else val
    data = await state.get_data()
    await state.clear()
    prod_repo = ProductRepository(session)
    existing = await prod_repo.get_by_name_in_category(data["name"], data["category_id"])
    if existing:
        await message.answer(
            f"❌ Product *{data['name']}* already exists in this category.",
            parse_mode="Markdown",
        )
        return

    product = Product(
        name=data["name"],
        unit=unit,
        category_id=data["category_id"],
    )
    await prod_repo.create(product)
    await message.answer(
        f"✅ Product *{product.name}* ({product.unit}) added.",
        reply_markup=admin_main_menu(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("admin_prod_edit_name:"))
async def product_edit_name_start(callback: CallbackQuery, state: FSMContext):
    prod_id = int(callback.data.split(":")[1]) # type: ignore
    await state.update_data(prod_id=prod_id)
    await callback.message.answer("✏️ Enter the *new product name*:", parse_mode="Markdown") # type: ignore
    await state.set_state(ProductStates.editing_name)
    await callback.answer()


@router.message(ProductStates.editing_name)
async def product_edit_name_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()
    repo = ProductRepository(session)
    prod = await repo.get_by_id(data["prod_id"])
    if not prod:
        await message.answer("❌ Product not found.")
        return
    prod.name = message.text.strip() # type: ignore
    await repo.update(prod)
    await message.answer(f"✅ Product renamed to *{prod.name}*.", parse_mode="Markdown")


@router.callback_query(F.data.startswith("admin_prod_edit_unit:"))
async def product_edit_unit_start(callback: CallbackQuery, state: FSMContext):
    prod_id = int(callback.data.split(":")[1]) # type: ignore
    await state.update_data(prod_id=prod_id)
    await callback.message.answer("📏 Enter the *new unit* (KG, Litre, Pcs…):", parse_mode="Markdown") # type: ignore
    await state.set_state(ProductStates.editing_unit)
    await callback.answer()


@router.message(ProductStates.editing_unit)
async def product_edit_unit_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()
    repo = ProductRepository(session)
    prod = await repo.get_by_id(data["prod_id"])
    if not prod:
        await message.answer("❌ Product not found.")
        return
    prod.unit = message.text.strip() # type: ignore
    await repo.update(prod)
    await message.answer(f"✅ Unit updated to *{prod.unit}*.", parse_mode="Markdown")


@router.callback_query(F.data.startswith("admin_prod_edit_cat:"))
async def product_edit_cat_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    prod_id = int(callback.data.split(":")[1]) # type: ignore
    await state.update_data(prod_id=prod_id)
    cat_repo = CategoryRepository(session)
    cats = await cat_repo.get_all()
    await callback.message.edit_text( # type: ignore
        "🗂 Select the *new category* for this product:",
        reply_markup=category_pick_keyboard(cats, "admin_prod_set_cat"),
        parse_mode="Markdown",
    )
    await state.set_state(ProductStates.editing_category)
    await callback.answer()


@router.callback_query(ProductStates.editing_category, F.data.startswith("admin_prod_set_cat:"))
async def product_edit_cat_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    new_cat_id = int(callback.data.split(":")[1]) # type: ignore
    data = await state.get_data()
    await state.clear()
    repo = ProductRepository(session)
    prod = await repo.get_by_id(data["prod_id"])
    if not prod:
        await callback.answer("Product not found.", show_alert=True)
        return
    prod.category_id = new_cat_id
    await repo.update(prod)
    cat_repo = CategoryRepository(session)
    cat = await cat_repo.get_by_id(new_cat_id)
    await callback.message.edit_text( # type: ignore
        f"✅ Product *{prod.name}* moved to *{cat.name if cat else '—'}*.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_prod_cancel")
async def product_edit_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Action cancelled.") # type: ignore
    await callback.answer()


@router.callback_query(F.data.startswith("admin_prod_deactivate:"))
async def product_deactivate(callback: CallbackQuery, session: AsyncSession):
    prod_id = int(callback.data.split(":")[1]) # type: ignore
    repo = ProductRepository(session)
    prod = await repo.get_by_id(prod_id)
    if not prod:
        await callback.answer("Not found.", show_alert=True)
        return
    await repo.soft_delete(prod)
    await callback.answer("🔴 Product deactivated.", show_alert=True)
    cat_repo = CategoryRepository(session)
    cat = await cat_repo.get_by_id(prod.category_id)
    status = "✅ Active" if prod.is_active else "❌ Inactive"
    await callback.message.edit_text( # type: ignore
        f"📦 *{prod.name}*\n\n📏 {prod.unit}\n🗂 {cat.name if cat else '—'}\nStatus: {status}",
        reply_markup=product_detail_keyboard(prod),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("admin_prod_activate:"))
async def product_activate(callback: CallbackQuery, session: AsyncSession):
    prod_id = int(callback.data.split(":")[1]) # type: ignore
    repo = ProductRepository(session)
    prod = await repo.get_by_id(prod_id)
    if not prod:
        await callback.answer("Not found.", show_alert=True)
        return
    await repo.activate(prod)
    await callback.answer("🟢 Product activated.", show_alert=True)
    cat_repo = CategoryRepository(session)
    cat = await cat_repo.get_by_id(prod.category_id)
    status = "✅ Active" if prod.is_active else "❌ Inactive"
    await callback.message.edit_text( # type: ignore
        f"📦 *{prod.name}*\n\n📏 {prod.unit}\n🗂 {cat.name if cat else '—'}\nStatus: {status}",
        reply_markup=product_detail_keyboard(prod),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("admin_prod_delete:"))
async def product_delete_confirm(callback: CallbackQuery, session: AsyncSession):
    prod_id = int(callback.data.split(":")[1]) # type: ignore
    repo = ProductRepository(session)
    prod = await repo.get_by_id(prod_id)
    if not prod:
        await callback.answer("Not found.", show_alert=True)
        return
    await safe_edit_text_or_caption(
        callback,
        f"⚠️ Are you sure you want to permanently *delete* product *{prod.name}*?\n"
        "This will completely remove it from the system.",
        reply_markup=confirm_delete_keyboard("prod", prod_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_prod:"))
async def product_delete_execute(callback: CallbackQuery, session: AsyncSession):
    prod_id = int(callback.data.split(":")[1]) # type: ignore
    repo = ProductRepository(session)
    prod = await repo.get_by_id(prod_id)
    if not prod:
        await callback.answer("Not found.", show_alert=True)
        return
    cat_id = prod.category_id
    await repo.delete(prod)
    products = await repo.get_all_by_category(cat_id)
    cat_repo = CategoryRepository(session)
    cat = await cat_repo.get_by_id(cat_id)
    await safe_edit_text_or_caption(
        callback,
        f"🗑 Product *{prod.name}* permanently deleted.\n\n"
        f"📦 *{cat.name if cat else '—'}* — Products ({len(products)})",
        reply_markup=product_list_keyboard(products, cat_id),
        parse_mode="Markdown",
    )
    await callback.answer("Product deleted.")


@router.callback_query(F.data.startswith("cancel_delete_prod:"))
async def product_delete_cancel(callback: CallbackQuery, session: AsyncSession):
    prod_id = int(callback.data.split(":")[1]) # type: ignore
    repo = ProductRepository(session)
    prod = await repo.get_by_id(prod_id)
    if not prod:
        await callback.answer()
        return
    cat_repo = CategoryRepository(session)
    cat = await cat_repo.get_by_id(prod.category_id)
    status = "✅ Active" if prod.is_active else "❌ Inactive"
    await callback.message.edit_text( # type: ignore
        f"📦 *{prod.name}*\n\n📏 {prod.unit}\n🗂 {cat.name if cat else '—'}\nStatus: {status}",
        reply_markup=product_detail_keyboard(prod),
        parse_mode="Markdown",
    )
    await callback.answer("Cancelled.")
