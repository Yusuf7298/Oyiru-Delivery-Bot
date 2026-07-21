from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.session import AsyncSessionLocal
from database.repositories.order_repository import OrderRepository
from database.models.order import OrderStatus
from keyboards.order_status import order_status_keyboard

router = Router()
async def send_orders(message: Message, orders):
    if not orders:
        await message.answer("No orders found.")
        return
    for order in orders:
        text = (
            f"📦 Order: {order.order_number}\n"
            f"👤 Customer: {order.customer.full_name}\n"
            f"📌 Status: {order.status.value}\n\n"
            "🛒 Products:\n"
        )

        for item in order.items:
            text += f"• {item.product.name} - {item.quantity} KG\n"

        builder = InlineKeyboardBuilder()
        builder.button(
            text="📄 Open Order",
            callback_data=f"open_order:{order.id}",
        )

        await message.answer(
            text,
            reply_markup=builder.as_markup(),
        )

@router.message(F.text == "📥 New Orders")
async def new_orders(message: Message):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel_user = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel_user:
            await message.answer("Hotel account not found.")
            return
        orders = await repo.get_new_orders(hotel_user.hotel.id)
        await send_orders(message, orders)

@router.message(F.text == "📦 Active Orders")
async def active_orders(message: Message):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel_user = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel_user:
            await message.answer("Hotel account not found.")
            return
        orders = await repo.get_active_orders(hotel_user.hotel.id)
        await send_orders(message, orders)

@router.message(F.text == "📜 Order History")
async def order_history(message: Message):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel_user = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel_user:
            await message.answer("Hotel account not found.")
            return
        orders = await repo.get_order_history(hotel_user.hotel.id)
        await send_orders(message, orders)

@router.callback_query(F.data.startswith("open_order:"))
async def open_order(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        order = await repo.get_order(order_id)
        if not order:
            await callback.answer("Order not found.", show_alert=True)
            return
        text = (
            f"📦 Order: {order.order_number}\n"
            f"👤 Customer: {order.customer.full_name}\n"
            f"📌 Status: {order.status.value}\n\n"
            "🛒 Products:\n"
        )

        for item in order.items:
            text += f"• {item.product.name} - {item.quantity} KG\n"
        await callback.message.edit_text( # type: ignore
            text,
            reply_markup=order_status_keyboard(order),
        )
    await callback.answer()

@router.callback_query(F.data.startswith("status:"))
async def update_order_status(callback: CallbackQuery):
    _, order_id, status = callback.data.split(":") # type: ignore
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        order = await repo.update_order_status(
            int(order_id),
            OrderStatus[status],
        )
        if not order:
            await callback.answer(
                "Order not found.",
                show_alert=True,
            )
            return
        await callback.bot.send_message( # type: ignore
            chat_id=order.customer.telegram_id,
            text=(
                "📦 Order Update\n\n"
                f"Order: {order.order_number}\n"
                f"New Status: {order.status.value}"
            ),
        )
        order = await repo.get_order(order.id)
        text = (
            f"📦 Order: {order.order_number}\n" # type: ignore
            f"👤 Customer: {order.customer.full_name}\n" # type: ignore
            f"📌 Status: {order.status.value}\n\n" # type: ignore
            "🛒 Products:\n"
        )

        for item in order.items: # type: ignore
            text += f"• {item.product.name} - {item.quantity} KG\n"
        await callback.message.edit_text( # type: ignore
            text,
            reply_markup=order_status_keyboard(order),
        )
    await callback.answer("✅ Status updated.")