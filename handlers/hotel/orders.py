import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.session import AsyncSessionLocal
from database.repositories.order_repository import OrderRepository
from database.models.order import OrderStatus
from keyboards.order_status import order_status_keyboard
from services.notification_service import notify_customer_status_update, notify_sales_managers
from filters.role_filter import RoleFilter
from states.store_manager import StoreManagerState

router = Router()
router.message.filter(RoleFilter(["hotel"]))
router.callback_query.filter(RoleFilter(["hotel"]))

async def send_orders(message: Message, orders):
    if not orders:
        await message.answer("No orders found.")
        return
    for order in orders:
        text = (
            f"📦 Order: {order.order_number}\n"
            f"👤 Customer: {order.customer.full_name}\n"
            f"📌 Status: {order.status.value}\n"
        )
        if order.driver_name:
            text += f"🚚 Driver: {order.driver_name}\n"
        text += "\n🛒 Products:\n"

        if order.file_path:
            text += f"• Direct Upload Document\n"
        else:
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
            parse_mode="Markdown"
        )

@router.message(F.text == "📥 New Orders")
async def new_orders(message: Message):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel_user = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel_user:
            await message.answer("Store Manager account not found.")
            return
        orders = await repo.get_new_orders(hotel_user.hotel_id) # type: ignore
        await send_orders(message, orders)

@router.message(F.text == "📦 Active Orders")
async def active_orders(message: Message):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel_user = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel_user:
            await message.answer("Store Manager account not found.")
            return
        orders = await repo.get_active_orders(hotel_user.hotel_id) # type: ignore
        await send_orders(message, orders)

@router.message(F.text == "📜 Order History")
async def order_history(message: Message):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel_user = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel_user:
            await message.answer("Store Manager account not found.")
            return
        orders = await repo.get_order_history(hotel_user.hotel_id) # type: ignore
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
            f"📦 *Order*: {order.order_number}\n"
            f"👤 *Customer*: {order.customer.full_name}\n"
            f"📌 *Status*: {order.status.value}\n"
        )
        if order.driver_name:
            text += f"🚚 *Driver*: {order.driver_name}\n"
        text += "\n🛒 *Products*:\n"

        if order.file_path:
            text += f"• Direct Upload Document\n"
        else:
            for item in order.items:
                text += f"• {item.product.name} - {item.quantity} KG\n"
        
        await callback.message.edit_text( # type: ignore
            text,
            reply_markup=order_status_keyboard(order),
            parse_mode="Markdown"
        )
    await callback.answer()

@router.callback_query(F.data.startswith("approve_prompt:"))
async def approve_prompt(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    await state.update_data(approving_order_id=order_id)
    await state.set_state(StoreManagerState.waiting_for_driver_name)
    await callback.message.answer("🚚 Please enter the name of the internal driver for this order:") # type: ignore
    await callback.answer()

# Handle Driver Name Input
@router.message(StoreManagerState.waiting_for_driver_name)
async def process_driver_name(message: Message, state: FSMContext):
    driver_name = message.text.strip() # type: ignore
    data = await state.get_data()
    order_id = data.get("approving_order_id")
    
    if not order_id:
        await message.answer("❌ Error: Order context lost. Please start over.")
        await state.clear()
        return

    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        order = await repo.assign_internal_driver(order_id, driver_name)
        if not order:
            await message.answer("❌ Order not found.")
            await state.clear()
            return
            
        # Notify Customer
        if order.customer:
            await notify_customer_status_update(message.bot, order, order.customer.telegram_id) # type: ignore
        await notify_sales_managers(message.bot, order, "Approved") # type: ignore
        await message.answer(f"✅ Order {order.order_number} approved and driver '{driver_name}' assigned successfully.")
        text = (
            f"📦 Order: {order.order_number}\n"
            f"👤 Customer: {order.customer.full_name}\n"
            f"📌 Status: {order.status.value}\n"
            f"🚚 Driver: {order.driver_name}\n\n"
            "🛒 Products:\n"
        )
        if order.file_path:
            text += f"• Direct Upload Document\n"
        else:
            for item in order.items:
                text += f"• {item.product.name} - {item.quantity} KG\n"
                
        await message.answer(
            text,
            reply_markup=order_status_keyboard(order),
            parse_mode="Markdown"
        )
        
    await state.clear()

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

        if order.customer:
            await notify_customer_status_update(callback.bot, order, order.customer.telegram_id) # type: ignore

        if OrderStatus[status] == OrderStatus.DELIVERED:
            await notify_sales_managers(callback.bot, order, "Delivered") # type: ignore
        order = await repo.get_order(order.id)
        text = (
            f"📦 Order: {order.order_number}\n" # type: ignore
            f"👤 Customer: {order.customer.full_name}\n" # type: ignore
            f"📌 Status: {order.status.value}\n" # type: ignore
        )
        if order.driver_name: # type: ignore
            text += f"🚚 Driver: {order.driver_name}\n" # type: ignore
        text += "\n🛒 Products:\n"

        if order.file_path: # type: ignore
            text += f"• Direct Upload Document\n"
        else:
            for item in order.items: # type: ignore
                text += f"• {item.product.name} - {item.quantity} KG\n"

        await callback.message.edit_text( # type: ignore
            text,
            reply_markup=order_status_keyboard(order),
            parse_mode="Markdown"
        )
    await callback.answer("✅ Status updated.")

@router.callback_query(F.data.startswith("hotel_view_file:"))
async def hotel_view_file(callback: CallbackQuery, session: AsyncSession): # type: ignore
    order_id = int(callback.data.split(":")[1]) # type: ignore
    repo = OrderRepository(session)
    order = await repo.get_order(order_id)
    
    if not order or not order.file_path:
        await callback.answer("File not found.", show_alert=True)
        return
        
    full_path = os.path.join(os.getcwd(), order.file_path)
    if not os.path.exists(full_path):
        await callback.answer("File not found on server disk.", show_alert=True)
        return
        
    await callback.answer("Sending document...")
    file_input = FSInputFile(full_path)
    await callback.message.reply_document(file_input, caption=f"📄 Document for Order: {order.order_number}") # type: ignore