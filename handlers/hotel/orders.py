from aiogram import Router, F
from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from database.models.order import OrderStatus
from database.repositories.order_repository import OrderRepository
from database.session import AsyncSessionLocal
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()
@router.message(F.text == "📥 New Orders")
async def new_orders(message: Message):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel:
            await message.answer("Hotel account not found.")
            return

        orders = await repo.get_new_orders(hotel.id)
        print("Orders:", )
        if not orders:
            await message.answer("No new orders.")
            return

        for order in orders:
            text = (
                f"🆕 {order.order_number}\n"
                f"Customer: {order.customer.full_name}\n"
                f"Status: {order.status.value}\n\n"
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
                reply_markup=builder.as_markup()
            )

@router.callback_query(F.data.startswith("open_order:"))
async def open_order(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        order = await repo.get_order(order_id)
        text = f"📦 Order #{order.order_number} Customer: {order.customer.full_name}  Status: {order.status.value} Products" # type: ignore

        for item in order.items: # type: ignore
            text += f"\n• {item.product.name} - {item.quantity} KG"

        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Under Review",
            callback_data=f"status:{order.id}:UNDER_REVIEW", # type: ignore
        )
        builder.button(
            text="❌ Cancel",
            callback_data=f"status:{order.id}:CANCELLED", # type: ignore
        )
        builder.adjust(1)
        if callback.message:
            await callback.message.edit_text( # type: ignore
                text,
                reply_markup=builder.as_markup(),)
    await callback.answer()

@router.callback_query(F.data.startswith("status:"))
async def change_status(callback: CallbackQuery):
    _, order_id, status = callback.data.split(":") # type: ignore
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        order = await repo.update_status(
            int(order_id),OrderStatus(status))
        if not order:
            await callback.answer("Order not found.")
            return
        await callback.bot.send_message( # type: ignore
            chat_id=order.customer.telegram_id,
            text=f"""
📦 Order Update

Order:
{order.order_number}

New Status:
{order.status.value}
"""
        )

        builder = InlineKeyboardBuilder()

        if order.status == OrderStatus.UNDER_REVIEW:

            builder.button(
                text="📦 Inventory Checking",
                callback_data=f"status:{order.id}:INVENTORY_CHECKING",
            )

        elif order.status == OrderStatus.INVENTORY_CHECKING:

            builder.button(
                text="👨‍🍳 Preparing",
                callback_data=f"status:{order.id}:PREPARING",
            )

        elif order.status == OrderStatus.PREPARING:

            builder.button(
                text="📦 Packed",
                callback_data=f"status:{order.id}:PACKED",
            )

        elif order.status == OrderStatus.PACKED:

            builder.button(
                text="🚚 Ready For Delivery",
                callback_data=f"status:{order.id}:READY_FOR_DELIVERY",
            )

        elif order.status == OrderStatus.READY_FOR_DELIVERY:

            builder.button(
                text="🛵 Out For Delivery",
                callback_data=f"status:{order.id}:OUT_FOR_DELIVERY",
            )

        elif order.status == OrderStatus.OUT_FOR_DELIVERY:

            builder.button(
                text="✅ Delivered",
                callback_data=f"status:{order.id}:DELIVERED",
            )

        await callback.message.edit_text( # type: ignore
            f"""
📦 {order.order_number}

Customer:
{order.customer.full_name}

Status:
{order.status.value}
""",
            reply_markup=builder.as_markup() if builder.buttons else None
        )

    await callback.answer("Updated")