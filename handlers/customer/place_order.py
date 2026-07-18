from aiogram import Router, F
from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from database.repositories.user_repository import UserRepository
from database.session import AsyncSessionLocal
from services.order_service import OrderService
from services.product_service import ProductService
from keyboards.customers import categories_keyboard,order_summary_keyboard
from states.order import PlaceOrderState
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()
@router.message(F.text == "📦 Place Order")
async def place_order(message: Message, state):
    async with AsyncSessionLocal() as session:
        service = ProductService(session)
        categories = await service.get_categories()
        await message.answer("Select one or more categories.",reply_markup=categories_keyboard(categories))
        await state.update_data(categories=[])
        await state.set_state(PlaceOrderState.selecting_categories)

@router.callback_query(PlaceOrderState.selecting_categories,F.data.startswith("cat_"))
async def select_category(callback: CallbackQuery,state: FSMContext):
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
        await callback.message.edit_reply_markup(reply_markup=categories_keyboard(categories,selected)) # type: ignore
    await callback.answer()

@router.callback_query(PlaceOrderState.selecting_categories,F.data == "continue_categories")
async def continue_categories(callback: CallbackQuery,state: FSMContext):
    data = await state.get_data()
    category_ids = data.get("categories", [])
    if not category_ids:
        await callback.answer("Select at least one category.",show_alert=True)
        return
    async with AsyncSessionLocal() as session:
        service = ProductService(session)
        products = await service.get_products(category_ids)

    await state.update_data(products=[{"id": p.id,"name": p.name,"category": p.category.name,} for p in products], current_product=0, order_items=[])
    first = products[0]
    await callback.message.answer( # type: ignore
        f"Product:\n\n"
        f"{first.name}\n\n"
        f"Enter quantity in KG.\n\n"
        f"Example:\n20"
    )
    await state.set_state(PlaceOrderState.entering_quantities)
    await callback.answer()

@router.message(PlaceOrderState.entering_quantities)
async def process_quantity(message: Message,state: FSMContext):
    try:
        quantity = float(message.text) # type: ignore
    except ValueError:
        await message.answer("Please enter a valid number.\n\nExample:\n20")
        return
    data = await state.get_data()
    products = data["products"]
    current = data["current_product"]
    order_items = data["order_items"]
    product = products[current]
    if quantity > 0:
        order_items.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "quantity": quantity
        })
    current += 1
    if current >= len(products):
        await state.update_data(order_items=order_items)
        summary = "📦 Order Summary\n\n"
        for item in order_items:
            summary += (
                f"• {item['product_name']} — "
                f"{item['quantity']} KG\n"
            )
        await message.answer(summary,reply_markup=order_summary_keyboard())
        await state.set_state(PlaceOrderState.order_summary)
        return

    await state.update_data(current_product=current,order_items=order_items)
    next_product = products[current]
    await message.answer(
        f"{next_product['name']}\n\n"
        "Enter quantity in KG.\n"
        "Enter 0 if you don't need this product."
    )


@router.callback_query(PlaceOrderState.order_summary,F.data == "submit_order")
async def submit_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession,):
    data = await state.get_data()
    user_repo = UserRepository(session)
    order_service = OrderService(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    if customer is None:
        await callback.answer("You are not registered.",show_alert=True)
        return
    if customer.hotel_id is None:
        await callback.answer("Your account is not assigned to a hotel.",show_alert=True)
        return

    order = await order_service.create_order(customer_id=customer.id,hotel_id=customer.hotel_id,items=data["order_items"],)
    await callback.message.answer( # type: ignore
        f"""
✅ Order Submitted Successfully
🆔 Order Number: {order.order_number}
🏨 Hotel: {customer.hotel.name}
📌 Status: {order.status.value}
Thank you for ordering from Oyiru Delivery.
"""
    )
    await state.clear()
    await callback.answer()