from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from database.models.returned_item import ReturnedItem
from database.models.order import OrderStatus
from database.repositories.order_repository import OrderRepository
from database.repositories.user_repository import UserRepository
from database.repositories.returned_item_repository import ReturnedItemRepository
from services.notification_service import notify_returned_products
from states.order import OrderState
from keyboards.customers import customer_menu, customer_reorder_menu
from filters.role_filter import RoleFilter

router = Router()
router.message.filter(RoleFilter(["customer", "hotel"]))
router.callback_query.filter(RoleFilter(["customer", "hotel"]))

_RECENT_LIMIT = 10   
def _order_picker_keyboard(orders: list):
    builder = InlineKeyboardBuilder()
    for order in orders:
        date_str = order.created_at.strftime("%d %b %Y") if order.created_at else "—"
        hotel    = order.hotel.name if order.hotel else "—"
        builder.button(
            text=f"🎉 {order.order_number}  ·  {date_str}  ·  {hotel}",
            callback_data=f"ret_order:{order.id}",
        )
    builder.button(text="❌ Cancel", callback_data="ret_cancel")
    builder.adjust(1)
    return builder.as_markup()


def _skip_photo_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Skip Photo", callback_data="ret_skip_photo")
    builder.adjust(1)
    return builder.as_markup()

@router.message(F.text.in_(["📦 Report Returns", "🔄 Report Returned Products"]))
async def start_return_flow(message: Message, state: FSMContext, session: AsyncSession):
    await _show_order_picker(message, state, session)


@router.callback_query(F.data == "ret_start")
async def start_return_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    await _show_order_picker(callback.message, state, session, # type: ignore
                             telegram_id=callback.from_user.id)


async def _show_order_picker(message: Message, state: FSMContext,
session: AsyncSession, telegram_id: int = None): # type: ignore
    tid = telegram_id or (message.from_user.id if message.from_user else message.chat.id)
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(tid)
    if not customer:
        await message.answer("❌ You are not registered.")
        return

    order_repo = OrderRepository(session)
    all_orders = await order_repo.get_customer_orders(customer.id)
    delivered  = [o for o in all_orders if o.status == OrderStatus.DELIVERED][:_RECENT_LIMIT]

    if not delivered:
        await message.answer(
            "📭 You have no delivered orders to report returns for."
        )
        return

    await state.set_state(OrderState.waiting_for_return_order)
    await message.answer(
        "📦 *Report Returned Products*\n\n"
        "Select the order you want to report returns for:",
        reply_markup=_order_picker_keyboard(delivered),
        parse_mode="Markdown",
    )

@router.callback_query(OrderState.waiting_for_return_order, F.data.startswith("ret_order:"))
async def order_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    order_id = int(callback.data.split(":")[1]) # type: ignore
    order_repo = OrderRepository(session)
    order = await order_repo.get_order(order_id)

    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return
    if order.status != OrderStatus.DELIVERED:
        await callback.answer("⚠️ Returns can only be reported for delivered orders.",
                              show_alert=True)
        return

    user_repo = UserRepository(session)
    me = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not me or order.customer_id != me.id:
        await callback.answer("⚠️ You can only report returns for your own orders.", show_alert=True)
        return

    await state.update_data(return_order_id=order_id)
    await state.set_state(OrderState.waiting_for_return_desc)
    await callback.message.edit_text( # type: ignore
        f"📦 Order: {order.order_number}\n"
        f"🏨 {order.hotel.name if order.hotel else '—'}\n\n"
        "✍️ Describe the returned items:\n\n"
        "_(Example: Tomato 5 KG – damaged, Rice 2 KG – wrong item)_",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(OrderState.waiting_for_return_desc)
async def receive_description(message: Message, state: FSMContext):
    description = message.text.strip() if message.text else ""
    if not description:
        await message.answer("❌ Description cannot be empty. Please describe the returned items:")
        return
    await state.update_data(return_description=description)
    await state.set_state(OrderState.waiting_for_return_photo)
    await message.answer(
        "📷 *Please send a proof photo of the returned items:*\n\n"
        "_(Upload a photo of the damaged or incorrect items for our Quality Control team, or tap ⏭ Skip Photo to proceed without a photo)_",
        reply_markup=_skip_photo_keyboard(),
        parse_mode="Markdown",
    )


@router.message(OrderState.waiting_for_return_photo,
                F.content_type == ContentType.PHOTO)
async def receive_photo(message: Message, state: FSMContext, session: AsyncSession):
    photo_file_id = message.photo[-1].file_id  # type: ignore # highest resolution
    await _save_and_notify(message, state, session, photo_file_id=photo_file_id)


@router.callback_query(OrderState.waiting_for_return_photo, F.data == "ret_skip_photo")
async def skip_photo(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    await _save_and_notify(callback.message, state, session,photo_file_id=None, telegram_id=callback.from_user.id) # type: ignore


@router.message(OrderState.waiting_for_return_photo)
async def invalid_photo_input(message: Message):
    await message.answer(
        "❌ Please send a photo or tap ⏭ Skip Photo.",
        reply_markup=_skip_photo_keyboard(),
        parse_mode="Markdown",
    )

async def _save_and_notify(message: Message, state: FSMContext,
                            session: AsyncSession, photo_file_id: str = None, # type: ignore
                            telegram_id: int = None): # type: ignore
    data = await state.get_data()
    order_id = data.get("return_order_id")
    description = data.get("return_description", "")
    await state.clear()

    tid = telegram_id or (message.from_user.id if message.from_user else message.chat.id)
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(tid)

    order_id_int = int(order_id) if order_id else None
    order_repo = OrderRepository(session)
    order = await order_repo.get_order(order_id_int) if order_id_int else None

    # Fallback to customer's latest order if specific order wasn't saved in state
    if not order and customer:
        order = await order_repo.get_last_order(customer.id)
        if order:
            order_id_int = order.id

    # Populate hotel if needed
    if customer and customer.hotel_id and not getattr(customer, "hotel", None):
        from database.repositories.hotel_repository import HotelRepository
        hotel_repo = HotelRepository(session)
        customer.hotel = await hotel_repo.get_by_id(customer.hotel_id)

    if order and order.hotel_id and not getattr(order, "hotel", None):
        from database.repositories.hotel_repository import HotelRepository
        hotel_repo = HotelRepository(session)
        order.hotel = await hotel_repo.get_by_id(order.hotel_id)
    elif order and customer and getattr(customer, "hotel", None) and not getattr(order, "hotel", None):
        order.hotel = customer.hotel

    returned = ReturnedItem(
        order_id=order_id_int,
        description=description,
        photo_file_id=photo_file_id,
    )
    ri_repo = ReturnedItemRepository(session)
    await ri_repo.create(returned)

    try:
        await notify_returned_products(
            message.bot, # type: ignore
            order=order,
            description=description,
            photo_file_id=photo_file_id,
            customer=customer,
        )
    except Exception as e:
        logger.error(f"Notification failed for return on order {order_id_int}: {e}")

    user_lang = getattr(customer, "language", "en") or "en"
    role_val = customer.role.value if customer and hasattr(customer.role, "value") else (str(customer.role) if customer else "")
    if role_val in ("hotel_admin", "hotel"):
        from keyboards.store_manager import hotel_admin_menu
        menu = hotel_admin_menu(user_lang)
    elif role_val == "store_manager":
        from keyboards.store_manager import store_manager_menu
        menu = store_manager_menu(user_lang)
    else:
        last = await order_repo.get_last_order(customer.id) if customer else None
        menu = customer_reorder_menu(user_lang) if last else customer_menu(user_lang)

    await message.answer(
        "✅ *Return Report Submitted!*\n\n"
        "Your return details and photo proof have been directly forwarded to our Quality Control team for review.",
        reply_markup=menu,
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "ret_cancel")
async def cancel_return(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    user_repo = UserRepository(session)
    customer  = await user_repo.get_by_telegram_id(callback.from_user.id)
    order_repo = OrderRepository(session)
    user_lang = getattr(customer, "language", "en") or "en"
    role_val = customer.role.value if customer and hasattr(customer.role, "value") else (str(customer.role) if customer else "")
    if role_val in ("hotel_admin", "hotel"):
        from keyboards.store_manager import hotel_admin_menu
        menu = hotel_admin_menu(user_lang)
    elif role_val == "store_manager":
        from keyboards.store_manager import store_manager_menu
        menu = store_manager_menu(user_lang)
    else:
        last = await order_repo.get_last_order(customer.id) if customer else None # type: ignore
        menu = customer_reorder_menu(user_lang) if last else customer_menu(user_lang)

    await callback.message.edit_text("❌ Return report cancelled.") # type: ignore
    await callback.message.answer("Choose an option:", reply_markup=menu) # type: ignore
    await callback.answer()