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
from sqlalchemy.ext.asyncio import AsyncSession
router = Router()
router.message.filter(RoleFilter(["hotel", "hotel_admin"]))
router.callback_query.filter(RoleFilter(["hotel", "hotel_admin"]))

from utils.i18n import t

async def send_orders(message: Message, orders, lang: str = "en"):
    if not orders:
        await message.answer(t("no_orders_found", lang))
        return
    for order in orders:
        text = (
            f"📦 *Order*: {order.order_number}\n"
            f"👤 *Customer*: {order.customer.full_name if order.customer else '—'}\n"
            f"📌 *Status*: {order.status.value}\n"
        )
        if order.driver_name:
            text += f"🚚 *Driver*: {order.driver_name}\n"
        text += "\n🛒 *Products / File*:\n"

        if order.file_path:
            text += f"• Direct Upload ({order.original_filename or 'File'})\n"
        else:
            for item in order.items:
                text += f"• {item.product.name if item.product else '—'} - {item.quantity} KG\n"

        builder = InlineKeyboardBuilder()
        builder.button(
            text=t("btn_open_order", lang),
            callback_data=f"open_order:{order.id}",
        )
        kb = builder.as_markup()

        sent = False
        if order.telegram_file_id:
            try:
                if order.file_type == "photo":
                    await message.answer_photo(photo=order.telegram_file_id, caption=text, reply_markup=kb, parse_mode="Markdown")
                else:
                    await message.answer_document(document=order.telegram_file_id, caption=text, reply_markup=kb, parse_mode="Markdown")
                sent = True
            except Exception:
                try:
                    if order.file_type == "photo":
                        await message.answer_photo(photo=order.telegram_file_id, caption=text, reply_markup=kb)
                    else:
                        await message.answer_document(document=order.telegram_file_id, caption=text, reply_markup=kb)
                    sent = True
                except Exception:
                    pass

        if not sent and order.file_path:
            import os
            from aiogram.types import FSInputFile
            candidate_paths = [
                os.path.join(os.getcwd(), order.file_path) if not os.path.isabs(order.file_path) else order.file_path,
                os.path.join(os.getcwd(), "uploads", os.path.basename(order.file_path)),
                order.file_path,
            ]
            valid_path = next((p for p in candidate_paths if os.path.exists(p)), None)
            if valid_path:
                try:
                    f = FSInputFile(valid_path)
                    if order.file_type == "photo":
                        await message.answer_photo(photo=f, caption=text, reply_markup=kb, parse_mode="Markdown")
                    else:
                        await message.answer_document(document=f, caption=text, reply_markup=kb, parse_mode="Markdown")
                    sent = True
                except Exception:
                    try:
                        f = FSInputFile(valid_path)
                        if order.file_type == "photo":
                            await message.answer_photo(photo=f, caption=text, reply_markup=kb)
                        else:
                            await message.answer_document(document=f, caption=text, reply_markup=kb)
                        sent = True
                    except Exception:
                        pass
        if not sent:
            try:
                await message.answer(
                    text,
                    reply_markup=kb,
                    parse_mode="Markdown"
                )
            except Exception:
                await message.answer(
                    text,
                    reply_markup=kb,
                )

NEW_ORDERS_BTNS = ["📥 New Orders", "📥 አዳዲስ ትዕዛዞች", "📥 Ajajawwan Haaraa"]
ACTIVE_ORDERS_BTNS = ["📦 Active Orders", "📦 የሚሰሩ ትዕዛዞች", "📦 Ajajawwan Hojii Irra Jiran"]
ORDER_HISTORY_BTNS = ["📜 Order History", "📜 የትዕዛዝ ታሪክ", "📜 Seenaa Ajajaa"]
HOTEL_EXPORT_BTNS = [
    "📊 Export Hotel Orders (Excel)", "📊 Export Hotel Orders",
    "📊 የሆቴል ትዕዛዞችን አውርድ (Excel)", "📊 የሆቴል ትዕዛዞችን አውርድ",
    "📊 Ajajawwan Hoteelaa Buusi (Excel)", "📊 Ajajawwan Hoteelaa Buusi"
]

@router.message(F.text.in_(HOTEL_EXPORT_BTNS))
async def export_hotel_orders(message: Message, lang: str = "en") -> None:
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel_user = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel_user or not hotel_user.hotel_id:
            await message.answer("❌ Hotel account not found.")
            return

        orders = await repo.get_hotel_all_orders(hotel_user.hotel_id)
        if not orders:
            await message.answer(t("no_orders_to_export", lang))
            return

        await message.answer(t("exporting_excel", lang))

        from database.repositories.hotel_repository import HotelRepository
        from utils.excel_export import generate_hotel_orders_excel
        from aiogram.types import BufferedInputFile
        from datetime import datetime, timezone

        hotel = await HotelRepository(session).get_by_id(hotel_user.hotel_id)
        hotel_name = hotel.name if hotel else "Hotel"

        xlsx_bytes = generate_hotel_orders_excel(hotel, orders)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        safe_name = "".join(c for c in hotel_name if c.isalnum() or c in ('_', '-'))
        filename = f"oyirubot_hotel_{safe_name}_{ts}.xlsx"
        doc = BufferedInputFile(xlsx_bytes, filename=filename)

        caption = t(
            "hotel_orders_export_caption",
            lang,
            hotel_name=hotel_name,
            count=len(orders),
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        )
        await message.answer_document(doc, caption=caption, parse_mode="Markdown")

@router.message(F.text.in_(NEW_ORDERS_BTNS))
async def new_orders(message: Message, lang: str = "en"):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel_user = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel_user:
            await message.answer("Store Manager account not found.")
            return
        orders = await repo.get_new_orders(hotel_user.hotel_id) # type: ignore
        await send_orders(message, orders, lang=lang)

@router.message(F.text.in_(ACTIVE_ORDERS_BTNS))
async def active_orders(message: Message, lang: str = "en"):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel_user = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel_user:
            await message.answer("Store Manager account not found.")
            return
        orders = await repo.get_active_orders(hotel_user.hotel_id) # type: ignore
        await send_orders(message, orders, lang=lang)

@router.message(F.text.in_(ORDER_HISTORY_BTNS))
async def order_history(message: Message, lang: str = "en"):
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        hotel_user = await repo.get_hotel_by_telegram(message.from_user.id) # type: ignore
        if not hotel_user:
            await message.answer("Store Manager account not found.")
            return
        orders = await repo.get_order_history(hotel_user.hotel_id) # type: ignore
        await send_orders(message, orders, lang=lang)

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
async def approve_prompt(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    async with AsyncSessionLocal() as session:
        from database.repositories.user_repository import UserRepository
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        user_repo = UserRepository(session)
        drivers = await user_repo.get_delivery_partners()
        if not drivers:
            await callback.answer("❌ No active delivery partners found.", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"🚗 {driver.full_name}",
                    callback_data=f"sm_pick_driver:{order_id}:{driver.id}",
                )]
                for driver in drivers
            ] + [[InlineKeyboardButton(text="❌ Cancel", callback_data=f"open_order:{order_id}")]]
        )
        await callback.message.edit_reply_markup(reply_markup=keyboard) # type: ignore
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