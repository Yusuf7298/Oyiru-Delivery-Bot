from aiogram import Router
from aiogram.types import Message
from aiogram import F
from database.repositories.order_repository import OrderRepository
from database.repositories.user_repository import UserRepository
router = Router()
@router.message(F.text == "📥 New Orders")
async def new_orders(message: Message, session):
    user_repo = UserRepository(session)
    order_repo = OrderRepository(session)
    hotel_user = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    orders = await order_repo.get_new_orders(hotel_user.hotel_id) # type: ignore
    if not orders:
        await message.answer("No new orders.")
        return

    for order in orders:
        await message.answer(
            f"""
🆕 New Order
🆔 {order.order_number}
📌 {order.status.value}
"""
        )