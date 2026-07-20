from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict
from database.session import AsyncSessionLocal
from database.repositories.user_repository import UserRepository
from services.product_service import ProductService
from services.order_service import OrderService
from keyboards.customers import categories_keyboard, order_summary_keyboard
from states.order import PlaceOrderState

router = Router()


@router.message(F.text == "📦 Place Order")
async def place_order(message: Message, state: FSMContext):
    async with AsyncSessionLocal() as session:
        service = ProductService(session)
        categories = await service.get_categories()
    await message.answer("Select one or more categories.",reply_markup=categories_keyboard(categories),)
    await state.update_data(categories=[])
    await state.set_state(PlaceOrderState.selecting_categories)

@router.callback_query(PlaceOrderState.selecting_categories,F.data.startswith("cat_"),)
async def select_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1]) # type: ignore
    data = await state.get_data()
    selected = data.get("categories", [])
    if category_id in selected:
        selected.remove(category_id)
    else:
        selected.append(category_id)
    await state.update_data(categories=selected)
    async with AsyncSessionLocal() as session:
        service = ProductService(session)
        categories = await service.get_categories()

    await callback.message.edit_reply_markup(reply_markup=categories_keyboard(categories, selected)) # type: ignore
    await callback.answer()

@router.callback_query(PlaceOrderState.selecting_categories,F.data == "continue_categories",)
async def continue_categories(callback: CallbackQuery, state: FSMContext,):
    data = await state.get_data()
    category_ids = data.get("categories", [])
    if not category_ids:
        await callback.answer("Select at least one category.",show_alert=True,)
        return

    async with AsyncSessionLocal() as session:
        service = ProductService(session)
        products = await service.get_products([category_ids[0]])
    await state.update_data(
        selected_categories=category_ids,
        category_index=0,
        category_products=[
            {
                "id": p.id,
                "name": p.name,
            }
            for p in products
        ],
        order_items=[],
    )

    text = (
        "📦 Enter quantities for this category.\n\n"
        "Write one product per line.\n\n"
    )

    for p in products:
        text += f"{p.name}=0\n"
    text += "\nExample:\nApple=20\nBanana=15"
    await callback.message.answer(text) # type: ignore
    await state.set_state(PlaceOrderState.entering_category_quantities)
    await callback.answer()

@router.message(PlaceOrderState.entering_category_quantities)
async def process_category_quantities(message: Message,state: FSMContext,):
    data = await state.get_data()
    products = data["category_products"]
    selected_categories = data["selected_categories"]
    category_index = data["category_index"]
    order_items = data["order_items"]
    product_map = {
        p["name"].lower(): p
        for p in products
    }
    for line in message.text.splitlines(): # type: ignore
        if "=" not in line:
            continue
        name, qty = line.split("=", 1)
        name = name.strip().lower()
        try:
            qty = float(qty.strip())
        except ValueError:
            continue
        if qty <= 0:
            continue
        if name in product_map:
            product = product_map[name]
            order_items.append(
                {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "quantity": qty,
                }
            )

    category_index += 1
    if category_index >= len(selected_categories):
        await state.update_data(order_items=order_items)
        summary = "📦 Order Summary\n\n"
        grouped = defaultdict(list)
        for item in order_items:
            grouped[item["product_name"]].append(item)
        for product_name, items in grouped.items():
            for item in items:
                summary += (
                    f"• {product_name} — "
                    f"{item['quantity']} KG\n"
                )
        await message.answer(summary,reply_markup=order_summary_keyboard(),)
        await state.set_state(PlaceOrderState.order_summary)
        return

    async with AsyncSessionLocal() as session:
        service = ProductService(session)
        products = await service.get_products([selected_categories[category_index]])

    await state.update_data(
        category_index=category_index,
        category_products=[
            {
                "id": p.id,
                "name": p.name,
            }
            for p in products
        ],
        order_items=order_items,
    )

    text = "📦 Next Category\n\n"
    for p in products:
        text += f"{p.name}=0\n"
    text += "\nExample:\nApple=20\nBanana=15"
    await message.answer(text)

@router.callback_query(PlaceOrderState.order_summary,F.data == "submit_order",)
async def submit_order(callback: CallbackQuery,state: FSMContext,session: AsyncSession,):
    data = await state.get_data()
    user_repo = UserRepository(session)
    order_service = OrderService(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    if customer is None:
        await callback.answer("You are not registered.",show_alert=True,)
        return

    if customer.hotel_id is None:
        await callback.answer("Your account is not assigned to a hotel.",show_alert=True,)
        return

    order = await order_service.create_order(
        customer_id=customer.id,
        hotel_id=customer.hotel_id,
        items=data["order_items"],
    )
    await callback.message.answer( # type: ignore
        f"""✅ Order Submitted Successfully

🆔 Order Number:
{order.order_number}

🏨 Hotel:
{customer.hotel.name}

📌 Status:
{order.status.value}

Thank you for ordering from Oyiru Delivery.
"""
    )
    await state.clear()
    await callback.answer()