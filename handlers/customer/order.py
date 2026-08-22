import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from database.repositories.user_repository import UserRepository
from database.repositories.category_repository import CategoryRepository
from database.repositories.product_repository import ProductRepository
from database.repositories.order_repository import OrderRepository
from services.order_service import OrderService
from services.notification_service import notify_new_order as notify_admin_new_order
from states.order import OrderState
from keyboards.customer.order import (
    category_select_keyboard,
    order_review_keyboard,
    skip_note_keyboard,
)
from keyboards.customers import customer_menu, customer_reorder_menu
from filters.role_filter import RoleFilter
from utils.i18n import t

router = Router()

router.message.filter(RoleFilter(["customer"]))
router.callback_query.filter(RoleFilter(["customer"]))

_QTY_RE = re.compile(
    r"^(.+?)\s*[-=:]\s*([0-9]+(?:\.[0-9]+)?)(?:\s*(?:kg|kilos|kilo|pcs|gm|g|l|liter|litre))?$"
    r"|"
    r"^(.+?)\s+([0-9]+(?:\.[0-9]+)?)(?:\s*(?:kg|kilos|kilo|pcs|gm|g|l|liter|litre))?$",
    re.IGNORECASE,
)

def _parse_line(line: str, product_map: dict) -> tuple:
    line = line.strip()
    m = _QTY_RE.match(line)
    if not m:
        raise ValueError(f"Cannot parse `{line}` — use: Name - Quantity")

    if m.group(1) is not None:
        raw_name, raw_qty = m.group(1).strip(), m.group(2).strip()
    else:
        raw_name, raw_qty = m.group(3).strip(), m.group(4).strip()

    try:
        qty = float(raw_qty)
    except ValueError:
        raise ValueError(f"Invalid quantity in `{line}`")

    if qty <= 0:
        raise ValueError(f"Quantity must be > 0 in `{line}`")

    norm = raw_name.lower()
    prod_id = product_map.get(norm)
    if prod_id is None:
        for pname, pid in product_map.items():
            if norm in pname or pname in norm:
                prod_id = pid
                break

    if prod_id is None:
        raise ValueError(f"Product `{raw_name}` not found in this category")

    return prod_id, qty


def _format_prompt(cat_name: str, products: list, invalid_lines: list = None, lang: str = "en") -> str:
    prod_list = "\n".join(f"  • {p.name} ({p.unit})" if getattr(p, "unit", None) else f"  • {p.name}" for p in products)
    
    examples = []
    sample_qtys = [20, 10, 15.5]
    for i, p in enumerate(products[:3]):
        qty = sample_qtys[i] if i < len(sample_qtys) else 5
        examples.append(f"`{p.name} - {qty}`")
    example_block = "\n".join(examples)
    
    if lang == "am":
        guide_title = "📝 *ትዕዛዝ እንዴት ማስገባት እንደሚችሉ ምሳሌ:*"
        guide_desc = "የዕቃውን ስም እና የሚፈልጉትን መጠን/ኪሎግራም (KG) በእያንዳንዱ መስመር በአንድ መልእክት ይላኩ:\n"
        hint = "_(እንዲሁም: `ስም 20` ወይም `ስም: 20` ወይም `ስም 20kg` ብለው መላክ ይችላሉ)_"
        fix_title = "⚠️ እነዚህን ስህተት የተገኘባቸውን መስመሮች ብቻ አስተካክለው እንደገና ይላኩ:\n\n"
        items_title = "የሚገኙ ዕቃዎች ዝርዝር:"
    elif lang == "om":
        guide_title = "📝 *Fakkeenya akkaataa itti ajajan:*"
        guide_desc = "Maqaa mi'ichaa fi hamma/kiilogiraama (KG) barbaaddan sarara adda addaa irratti ergaa:\n"
        hint = "_(Akkasumas: `Maqaa 20` yookiin `Maqaa: 20` yookiin `Maqaa 20kg` jechuun erguu dandeessu)_"
        fix_title = "⚠️ Kanneen dogoggora qaban qofa sirreessuun deebisaa ergaa:\n\n"
        items_title = "Mi'aawwan Argaman:"
    else:
        guide_title = "📝 *Example of how to enter your order:*"
        guide_desc = "Send each item and its kilogram (KG) or quantity on a new line in one message:\n"
        hint = "_(You can also type: `Name 20` or `Name: 20` or `Name 20kg`)_"
        fix_title = "⚠️ Fix these lines only (copy, correct, and send again):\n\n"
        items_title = "Available Items in this Category:"

    body = (
        f"📦 *{cat_name}*\n\n"
        f"📋 {items_title}\n"
        f"{prod_list}\n\n"
        f"{guide_title}\n"
        f"{guide_desc}"
        f"{example_block}\n\n"
        f"{hint}"
    )

    if invalid_lines:
        bad = "\n".join(f"  ❌ {ln}" for ln in invalid_lines)
        body = (
            f"{fix_title}"
            f"{bad}\n\n──────────────\n"
        ) + body

    return body


@router.message(F.text.in_(["🧺 Category Order", "🧺 Listing Order", "🧺 New Category Order", "🧺 የዕቃዎች ምድብ", "🧺 Kutaalee Mi'aa"]))
async def start_category_order(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
    await state.clear()
    cats = await CategoryRepository(session).get_active_categories()
    if not cats:
        await message.answer("❌ No product categories are available right now.")
        return

    await state.update_data(selected_cat_ids=[], quantities={}, language=lang)
    await message.answer(
        "🧺 New Order\n\n"
        "Select the categories you want to order from, then tap ➡️ Continue.",
        reply_markup=category_select_keyboard(cats, [], lang=lang),
        parse_mode="Markdown",
    )
    await state.set_state(OrderState.selecting_categories)

@router.callback_query(OrderState.selecting_categories, F.data.startswith("toggle_cat:"))
async def toggle_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = "en"):
    cat_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected: list = data.get("selected_cat_ids", [])

    if cat_id in selected:
        selected.remove(cat_id)
    else:
        selected.append(cat_id)
    await state.update_data(selected_cat_ids=selected)
    cats = await CategoryRepository(session).get_active_categories()
    await callback.message.edit_reply_markup(
        reply_markup=category_select_keyboard(cats, selected, lang=lang)
    )
    await callback.answer()

@router.callback_query(OrderState.selecting_categories, F.data == "cats_done")
async def categories_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = "en"):
    data = await state.get_data()
    selected: list = data.get("selected_cat_ids", [])

    if not selected:
        await callback.answer("⚠️ Please select at least one category.", show_alert=True)
        return
    prod_repo = ProductRepository(session)
    valid = []
    quantities = {}
    for cid in selected:
        prods = await prod_repo.get_products_by_category(cid)
        if prods:
            valid.append(cid)
            for p in prods:
                quantities[str(p.id)] = 0.0

    if not valid:
        await callback.answer("⚠️ Selected categories have no active products.", show_alert=True)
        return

    await state.update_data(selected_cat_ids=valid, cat_index=0, quantities=quantities, language=lang)
    await state.set_state(OrderState.entering_quantities)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _send_category_prompt(callback.bot, callback.from_user.id, state, session, lang=lang)
    try:
        await callback.answer()
    except Exception:
        pass


async def _send_category_prompt(bot, chat_id: int, state: FSMContext, session: AsyncSession, invalid_lines: list = None, lang: str = "en"):
    data = await state.get_data()
    user_lang = data.get("language", lang) or lang
    selected: list = data["selected_cat_ids"]
    idx: int = data["cat_index"]
    if idx >= len(selected):
        await bot.send_message(
            chat_id=chat_id,
            text=(
                "📝 Optional Note\n\n"
                "Add a note for this order _(e.g. Urgent / Deliver before 9 AM)_\n\n"
                "Or tap ⏭️ Skip Note to continue."
            ),
            reply_markup=skip_note_keyboard(lang=user_lang),
            parse_mode="Markdown",
        )
        await state.set_state(OrderState.entering_note)
        return

    cat_id = selected[idx]
    cat = await CategoryRepository(session).get_by_id(cat_id)
    products = await ProductRepository(session).get_products_by_category(cat_id)
    progress = f"({idx + 1}/{len(selected)})"
    text = _format_prompt(f"{cat.name} {progress}", products, invalid_lines, lang=user_lang)
    await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")


@router.message(OrderState.entering_quantities)
async def receive_quantities(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
    data = await state.get_data()
    user_lang = data.get("language", lang) or lang
    selected: list = data["selected_cat_ids"]
    idx: int = data["cat_index"]
    quantities: dict = data.get("quantities", {})
    cat_id = selected[idx]
    products = await ProductRepository(session).get_products_by_category(cat_id)
    product_map = {p.name.lower(): p.id for p in products}
    lines = [ln.strip() for ln in message.text.splitlines() if ln.strip()]
    if not lines:
        await message.answer("❌ Your message is empty. Please enter the quantities.")
        return

    parsed: dict = {}
    invalid: list = []

    for line in lines:
        try:
            prod_id, qty = _parse_line(line, product_map)
            parsed[prod_id] = qty
        except ValueError as exc:
            invalid.append(str(exc))

    if invalid:
        await _send_category_prompt(
            message.bot, message.from_user.id, state, session,
            invalid_lines=invalid,
            lang=user_lang,
        )
        return
    for prod_id, qty in parsed.items():
        quantities[str(prod_id)] = qty

    await state.update_data(quantities=quantities, cat_index=idx + 1)
    await _send_category_prompt(message.bot, message.from_user.id, state, session, lang=user_lang)


@router.message(OrderState.entering_note)
async def receive_note(message: Message, state: FSMContext, session: AsyncSession):
    raw = message.text.strip()
    note = None if raw in ("⏭️ Skip Note", "/skip", "skip", "—") else raw
    await state.update_data(note=note)
    data = await state.get_data()
    if data.get("order_method") == "upload":
        from handlers.customer.upload_order import show_upload_review
        await show_upload_review(message, state, session)
    else:
        await state.set_state(OrderState.reviewing_order)
        await _send_review(message, state, session)


async def _send_review(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    quantities: dict = data.get("quantities", {})
    note = data.get("note")
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(
        message.from_user.id if message.from_user else message.chat.id
    )
    hotel_name = customer.hotel.name if (customer and customer.hotel) else "—"
    prod_repo = ProductRepository(session)
    lines = []
    for prod_id_str, qty in quantities.items():
        if float(qty) < 0:
            continue
        prod = await prod_repo.get_by_id(int(prod_id_str))
        if prod:
            lines.append(f"• {prod.name} — {qty} KG")

    if not lines:
        await message.answer(
            "⚠️ No products found in selected categories. Please start a new order."
        )
        await state.clear()
        return
    text = (
        "📋 Order Review\n\n"
        f"🏨 Hotel: {hotel_name}\n"
        f"👤 Customer: {customer.full_name if customer else '—'}\n\n"
        f"🛒 *Products:*\n" + "\n".join(lines) + "\n\n"
        f"📝 Note: {note or '—'}"
    )
    await message.answer(text, reply_markup=order_review_keyboard(), parse_mode="Markdown")

@router.callback_query(OrderState.reviewing_order, F.data == "order_edit_note")
async def edit_note(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 Enter a new note, or tap ⏭️ Skip Note to remove it:",
        reply_markup=skip_note_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(OrderState.entering_note)
    await callback.answer()

@router.callback_query(OrderState.reviewing_order, F.data == "order_submit")
async def submit_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    quantities: dict = data.get("quantities", {})
    note = data.get("note")
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not customer or not customer.hotel_id:
        await callback.answer("❌ You are not associated with a hotel.", show_alert=True)
        return
    items = [
        {"product_id": int(pid), "quantity": float(qty)}
        for pid, qty in quantities.items()
        if float(qty) > 0
    ]
    if not items:
        await callback.answer("❌ Please enter at least one product with quantity > 0.", show_alert=True)
        return

    await callback.answer("Order submitted!")

    order_service = OrderService(session)
    order = await order_service.create_order(
        customer_id=customer.id,
        hotel_id=customer.hotel_id,
        items=items,
        note=note,
    )
    await state.clear()
    try:
        await notify_admin_new_order(callback.bot, order, customer)
    except Exception as exc:
        logger.error(f"Notification failed for {order.order_number}: {exc}")
    last = await OrderRepository(session).get_last_order(customer.id)
    menu = customer_reorder_menu() if last else customer_menu()

    await callback.message.edit_text(
        f"✅ *Order Submitted!*\n\n"
        f"🆔 Order Number: `{order.order_number}`\n"
        f"🏨 Hotel: {customer.hotel.name if customer.hotel else '—'}\n"
        f"📌 Status: {order.status.value}",
        parse_mode="Markdown",
    )
    await callback.message.answer("Choose an option:", reply_markup=menu)


@router.callback_query(F.data == "order_cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    order_repo = OrderRepository(session)
    last = await order_repo.get_last_order(customer.id) if customer else None
    menu = customer_reorder_menu() if last else customer_menu()
    await callback.message.edit_text("❌ Order cancelled.")
    await callback.message.answer("Main menu:", reply_markup=menu)
    await callback.answer()

@router.message(F.text.in_(["🔄 Repeat Last Order", "🔄 Reorder Last Order", "🔄 ያለፈውን ትዕዛዝ ድገም", "🔄 Ajaja Darbe Irra Deebi'i"]))
async def repeat_last_order(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(message.from_user.id)
    if not customer:
        await message.answer("❌ You are not registered.")
        return

    order_repo = OrderRepository(session)
    last = await order_repo.get_last_order(customer.id)
    if not last:
        await message.answer("❌ You have not placed any orders yet.")
        return

    if last.file_path or last.telegram_file_id:
        await state.update_data(
            order_method="upload",
            file_path=last.file_path,
            telegram_file_id=last.telegram_file_id,
            file_type=last.file_type,
            note=last.note,
        )
        from states.order import OrderState as OS
        await state.set_state(OS.reviewing_uploaded_order)
        from handlers.customer.upload_order import show_upload_review
        await show_upload_review(message, state, session)
        return
    prod_repo = ProductRepository(session)
    quantities: dict = {}
    selected_cat_ids: list = []
    seen: set = set()

    for item in last.items:
        prod = await prod_repo.get_by_id(item.product_id)
        if prod:
            quantities[str(prod.id)] = item.quantity
            if prod.category_id not in seen:
                selected_cat_ids.append(prod.category_id)
                seen.add(prod.category_id)

    await state.update_data(
        selected_cat_ids=selected_cat_ids,
        cat_index=len(selected_cat_ids),
        quantities=quantities,
        note=last.note,
    )
    await state.set_state(OrderState.reviewing_order)
    await _send_review(message, state, session)


@router.message(F.text.in_(["🔙 Back", "🔙 ተመለስ", "🔙 Duubatti"]))
async def back_to_menu(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(message.from_user.id)
    order_repo = OrderRepository(session)
    last = await order_repo.get_last_order(customer.id) if customer else None
    menu = customer_reorder_menu() if last else customer_menu()
    await message.answer("Main menu:", reply_markup=menu)


@router.message(F.text.in_(["👤 Profile", "👤 My Profile", "👤 መገለጫ", "👤 መገለጫዬ", "👤 Profaayilii Koo"]))
async def customer_profile(message: Message, session: AsyncSession, lang: str = "en"):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("User profile not found.")
        return
    
    hotel_name = user.hotel.name if user.hotel else "N/A"
    lang_name = "English" if user.language == "en" else ("አማርኛ" if user.language == "am" else "Afaan Oromoo")
    
    profile_text = (
        f"👤 *Profile*\n\n"
        f"👤 *Name*: {user.full_name}\n"
        f"📱 *Phone*: {user.phone or 'N/A'}\n"
        f"🏨 *Hotel*: {hotel_name}\n"
        f"🌐 *Language*: {lang_name}\n"
        f"📌 *Role*: {user.role.value if hasattr(user.role, 'value') else user.role}"
    )
    await message.answer(profile_text, parse_mode="Markdown")

@router.message(F.text.in_(["❓ Help", "❓ እርዳታ", "❓ Gargaarsa"]))
async def customer_help(message: Message, lang: str = "en"):
    await message.answer(t("help_guide", lang), parse_mode="Markdown")
