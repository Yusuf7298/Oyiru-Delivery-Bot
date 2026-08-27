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
from keyboards.store_manager import store_manager_menu
from filters.role_filter import RoleFilter
from utils.i18n import t

router = Router()

router.message.filter(RoleFilter(["customer", "hotel"]))
router.callback_query.filter(RoleFilter(["customer", "hotel"]))

_QTY_RE = re.compile(
    r"^(?P<name>.+?)\s*(?:[-=:]|\s)\s*(?P<qty>[0-9]+(?:\.[0-9]+)?)\s*(?P<unit>[a-zA-Z\u1200-\u137F]*)$",
    re.IGNORECASE,
)

def _parse_line(line: str, product_catalog_map: dict = None) -> dict:
    line = line.strip()
    if not line:
        return None  # type: ignore

    m = _QTY_RE.match(line)
    if not m:
        # Check reverse format: e.g. "60 Habab" or "60kg Habab"
        m2 = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z\u1200-\u137F]*)\s*(?:[-=:]|\s)\s*(.+)$", line)
        if m2:
            raw_qty, raw_unit, raw_name = m2.group(1), m2.group(2), m2.group(3)
        else:
            raise ValueError(f"Missing quantity in `{line}` — use format: `Name Quantity` (e.g. `{line} 10` or `{line} - 10kg`)")
    else:
        raw_name = m.group("name").strip()
        raw_qty = m.group("qty").strip()
        raw_unit = m.group("unit").strip() if m.group("unit") else ""

    try:
        qty = float(raw_qty)
    except ValueError:
        raise ValueError(f"Invalid quantity in `{line}`")

    if qty <= 0:
        raise ValueError(f"Quantity must be > 0 in `{line}`")

    # Clean unit
    unit_lower = raw_unit.lower()
    if unit_lower in ("kg", "kilos", "kilo", "ኪሎ"):
        unit_str = "KG"
    elif unit_lower in ("pcs", "pc", "ፍሬ", "ቁራጭ"):
        unit_str = "Pcs"
    elif unit_lower in ("box", "boxes", "ካርቶን"):
        unit_str = "Box"
    elif raw_unit:
        unit_str = raw_unit.upper()
    else:
        unit_str = "KG"

    # Match existing catalog product if available
    prod_id = None
    prod_name = raw_name
    if product_catalog_map:
        norm = raw_name.lower()
        if norm in product_catalog_map:
            p = product_catalog_map[norm]
            prod_id = p.id
            prod_name = p.name
            if not raw_unit and getattr(p, "unit", None):
                unit_str = p.unit
        else:
            for cname, p in product_catalog_map.items():
                if norm == cname or norm in cname or cname in norm:
                    prod_id = p.id
                    prod_name = p.name
                    if not raw_unit and getattr(p, "unit", None):
                        unit_str = p.unit
                    break

    return {
        "product_id": prod_id,
        "product_name": prod_name,
        "quantity": qty,
        "unit": unit_str,
    }


def _format_prompt(cat_names_str: str, invalid_lines: list = None, lang: str = "en") -> str:
    if lang == "am":
        title = f"🧺 *የዕቃዎች ትዕዛዝ ማዘዣ* ({cat_names_str})"
        guide = (
            "✍️ *የሚፈልጓቸውን ዕቃዎች እና መጠናቸውን በአንድ መልእክት በእያንዳንዱ መስመር ይጻፉ:*\n\n"
            "📝 *ምሳሌ:*\n"
            "`Habab 60`\n"
            "`Papaya 100`\n"
            "`Shinkurt 40`\n"
            "`Kororima 5`\n"
            "`Gebs duket 6`\n\n"
            "_(የፈለጉትን ዕቃ እና ኪሎ/መጠን መጻፍ ይችላሉ፣ ለምሳሌ: `ስም 20` ወይም `ስም: 20` ወይም `ስም 20kg`)_"
        )
        fix_title = "⚠️ እባክዎን እነዚህን መስመሮች ብቻ መጠን/ቁጥር ጨምረው እንደገና ይላኩ:\n\n"
    elif lang == "om":
        title = f"🧺 *Galmee Ajaja Mi'aa* ({cat_names_str})"
        guide = (
            "✍️ *Mi'aawwan barbaaddan hundaafi hamma isaanii ergaa tokkoon sarara adda addaa irratti barreessaa:*\n\n"
            "📝 *Fakkeenya:*\n"
            "`Habab 60`\n"
            "`Papaya 100`\n"
            "`Shinkurt 40`\n"
            "`Kororima 5`\n"
            "`Gebs duket 6`\n\n"
            "_(Mi'aawwan barbaaddan hunda barreessuu dandeessu: `Maqaa 20` yookiin `Maqaa: 20` yookiin `Maqaa 20kg`)_"
        )
        fix_title = "⚠️ Maaloo kanneen dogoggora qaban qofa sirreessuun deebisaa ergaa:\n\n"
    else:
        title = f"🧺 *Order Items Entry* ({cat_names_str})"
        guide = (
            "✍️ *Send all your order items and quantities in one message:*\n"
            "_(Each item on a new line)_\n\n"
            "📝 *Example:*\n"
            "`Habab 60`\n"
            "`Papaya 100`\n"
            "`Shinkurt 40`\n"
            "`Kororima 5`\n"
            "`Gebs duket 6`\n\n"
            "_(You can enter any product and quantity: `Name 20`, `Name: 20`, or `Name - 20kg`)_"
        )
        fix_title = "⚠️ Please specify quantity for these lines and send again:\n\n"

    body = f"{title}\n\n{guide}"
    if invalid_lines:
        bad = "\n".join(f"  ❌ {ln}" for ln in invalid_lines)
        body = f"{fix_title}{bad}\n\n──────────────\n" + body

    return body


@router.message(F.text.in_(["🧺 Category Order", "🧺 Listing Order", "🧺 New Category Order", "🧺 የዕቃዎች ምድብ", "🧺 Kutaalee Mi'aa"]))
async def start_category_order(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
    await state.clear()
    cats = await CategoryRepository(session).get_active_categories()
    if not cats:
        await message.answer("❌ No product categories are available right now.")
        return

    await state.update_data(selected_cat_ids=[], items=[], language=lang)
    await message.answer(
        "🧺 *New Order*\n\n"
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

    cat_repo = CategoryRepository(session)
    selected_cats = []
    for cid in selected:
        cat = await cat_repo.get_by_id(cid)
        if cat:
            selected_cats.append(cat)

    cat_names_str = ", ".join(c.name for c in selected_cats) if selected_cats else "General"
    await state.update_data(selected_cat_ids=selected, cat_names_str=cat_names_str, language=lang)
    await state.set_state(OrderState.entering_quantities)
    try:
        await callback.message.delete()
    except Exception:
        pass

    text = _format_prompt(cat_names_str, lang=lang)
    await callback.message.answer(text, parse_mode="Markdown")
    try:
        await callback.answer()
    except Exception:
        pass


@router.message(OrderState.entering_quantities)
async def receive_quantities(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
    data = await state.get_data()
    user_lang = data.get("language", lang) or lang
    cat_names_str = data.get("cat_names_str", "Order Items")

    lines = [ln.strip() for ln in (message.text or "").splitlines() if ln.strip()]
    if not lines:
        await message.answer("❌ Your message is empty. Please enter your order items.")
        return

    prod_repo = ProductRepository(session)
    all_prods = await prod_repo.get_active_products()
    catalog_map = {p.name.lower(): p for p in all_prods}

    parsed_items: list = []
    invalid: list = []

    for line in lines:
        try:
            item_data = _parse_line(line, catalog_map)
            if item_data:
                parsed_items.append(item_data)
        except ValueError as exc:
            invalid.append(str(exc))

    if invalid:
        await message.answer(
            _format_prompt(cat_names_str, invalid_lines=invalid, lang=user_lang),
            parse_mode="Markdown",
        )
        return

    if not parsed_items:
        await message.answer("❌ No valid items could be parsed. Please try again.")
        return

    await state.update_data(items=parsed_items)
    await state.set_state(OrderState.entering_note)
    await message.answer(
        "📝 *Optional Delivery Note*\n\n"
        "Add a note for this order _(e.g. Urgent / Deliver before 9 AM)_\n\n"
        "Or tap ⏭️ Skip Note to proceed.",
        reply_markup=skip_note_keyboard(lang=user_lang),
        parse_mode="Markdown",
    )


@router.message(OrderState.entering_note)
async def receive_note(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
    raw = (message.text or "").strip()
    note = None if raw in ("⏭️ Skip Note", "/skip", "skip", "—", "⏭️ ማስታወሻ ይለፉ", "⏭️ Yaadannoo Dhiisi") else raw
    await state.update_data(note=note)
    data = await state.get_data()
    if data.get("order_method") == "upload":
        from handlers.customer.upload_order import show_upload_review
        await show_upload_review(message, state, session, lang=lang)
    else:
        await state.set_state(OrderState.reviewing_order)
        await _send_review(message, state, session, lang=lang)


async def _send_review(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
    data = await state.get_data()
    items: list = data.get("items", [])
    note = data.get("note")
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(
        message.from_user.id if message.from_user else message.chat.id
    )
    hotel_name = customer.hotel.name if (customer and customer.hotel) else "—"

    lines = []
    total_qty = 0.0
    for item in items:
        pname = item.get("product_name") or "Product"
        qty = item.get("quantity", 0.0)
        unit = item.get("unit", "KG")
        lines.append(f"• {pname} — {qty} {unit}")
        try:
            total_qty += float(qty)
        except (ValueError, TypeError):
            pass

    if not lines:
        await message.answer(
            "⚠️ No order items found. Please start a new order."
        )
        await state.clear()
        return

    text = (
        "📋 *Order Review*\n\n"
        f"🏨 Hotel: *{hotel_name}*\n"
        f"👤 Customer: *{customer.full_name if customer else '—'}*\n\n"
        f"🛒 *Products ({len(items)} items — Total {total_qty:.1f} KG):*\n" + "\n".join(lines) + "\n\n"
        f"📝 Note: {note or '—'}"
    )
    await message.answer(text, reply_markup=order_review_keyboard(lang=lang), parse_mode="Markdown")

@router.callback_query(OrderState.reviewing_order, F.data == "order_edit_note")
async def edit_note(callback: CallbackQuery, state: FSMContext, lang: str = "en"):
    await callback.message.answer(
        "📝 Enter a new note, or tap ⏭️ Skip Note to remove it:",
        reply_markup=skip_note_keyboard(lang=lang),
        parse_mode="Markdown",
    )
    await state.set_state(OrderState.entering_note)
    await callback.answer()

@router.callback_query(OrderState.reviewing_order, F.data == "order_submit")
async def submit_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = "en"):
    data = await state.get_data()
    items: list = data.get("items", [])
    note = data.get("note")
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not customer or not customer.hotel_id:
        await callback.answer("❌ You are not associated with a hotel.", show_alert=True)
        return

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
    role_val = customer.role.value if hasattr(customer.role, "value") else str(customer.role)
    if role_val == "hotel":
        menu = store_manager_menu(lang)
    else:
        menu = customer_reorder_menu(lang) if last else customer_menu(lang)

    await callback.message.edit_text(
        f"✅ *Order Submitted!*\n\n"
        f"🆔 Order Number: `{order.order_number}`\n"
        f"🏨 Hotel: {customer.hotel.name if customer.hotel else '—'}\n"
        f"📌 Status: {order.status.value}",
        parse_mode="Markdown",
    )
    await callback.message.answer("Choose an option:", reply_markup=menu)


@router.callback_query(F.data == "order_cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = "en"):
    await state.clear()
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    order_repo = OrderRepository(session)
    last = await order_repo.get_last_order(customer.id) if customer else None
    role_val = customer.role.value if customer and hasattr(customer.role, "value") else (str(customer.role) if customer else "")
    if role_val == "hotel":
        menu = store_manager_menu(lang)
    else:
        menu = customer_reorder_menu(lang) if last else customer_menu(lang)
    await callback.message.edit_text("❌ Order cancelled.")
    await callback.message.answer("Main menu:", reply_markup=menu)
    await callback.answer()

@router.message(F.text.in_(["🔄 Repeat Last Order", "🔄 Reorder Last Order", "🔄 ያለፈውን ትዕዛዝ ድገም", "🔄 Ajaja Darbe Irra Deebi'i"]))
async def repeat_last_order(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
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
        await show_upload_review(message, state, session, lang=lang)
        return

    items: list = []
    for item in last.items:
        pname = (item.product.name if item.product else getattr(item, "product_name", None)) or "Product"
        punit = getattr(item.product, "unit", getattr(item, "unit", "KG")) or "KG"
        items.append({
            "product_id": item.product_id,
            "product_name": pname,
            "quantity": item.quantity,
            "unit": punit,
        })

    await state.update_data(items=items, note=last.note)
    await state.set_state(OrderState.reviewing_order)
    await _send_review(message, state, session, lang=lang)


@router.message(F.text.in_(["🔙 Back", "🔙 ተመለስ", "🔙 Duubatti"]))
async def back_to_menu(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
    await state.clear()
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(message.from_user.id)
    order_repo = OrderRepository(session)
    last = await order_repo.get_last_order(customer.id) if customer else None
    role_val = customer.role.value if customer and hasattr(customer.role, "value") else (str(customer.role) if customer else "")
    if role_val == "hotel":
        menu = store_manager_menu(lang)
    else:
        menu = customer_reorder_menu(lang) if last else customer_menu(lang)
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
