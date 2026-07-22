from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.session import AsyncSessionLocal
from database.repositories.order_repository import OrderRepository

from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(F.text == "📦 Available Deliveries")
async def available_deliveries(message: Message):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        orders = await repo.get_available_deliveries()
        if not orders:
            await message.answer(
                "No available deliveries."
            )
            return
        for order in orders:
            text = (
                f"📦 {order.order_number}\n"
                f"🏨 {order.hotel.name}\n"
                f"👤 {order.customer.full_name}\n"
                f"📌 {order.status.value}\n\n"
            )
            for item in order.items:
                text += (
                    f"• {item.product.name}"
                    f" - {item.quantity} KG\n"
                )
            builder = InlineKeyboardBuilder()
            builder.button(
                text="✅ Accept Delivery",
                callback_data=f"accept_delivery:{order.id}",
            )
            await message.answer(
                text,
                reply_markup=builder.as_markup(),
            )