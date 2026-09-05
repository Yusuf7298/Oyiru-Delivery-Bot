from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.order_repository import OrderRepository
from database.repositories.user_repository import UserRepository
from services.notification_service import notify_quality_control, notify_sales_managers
from states.order import OrderState
from keyboards.customers import customer_menu, customer_reorder_menu
from filters.role_filter import RoleFilter
from database.models.order import  OrderStatus
from utils.i18n import t

router = Router()
router.message.filter(RoleFilter(["customer", "hotel"]))
router.callback_query.filter(RoleFilter(["customer", "hotel"]))

def _skip_feedback_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Skip Feedback", callback_data="rating_skip_feedback")
    builder.adjust(1)
    return builder.as_markup()

def _skip_returns_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Skip Returns", callback_data="rating_skip_returns")
    builder.adjust(1)
    return builder.as_markup()

def _skip_photo_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Skip Photo", callback_data="rating_skip_photo")
    builder.adjust(1)
    return builder.as_markup()

def _returns_prompt() -> str:
    return (
        "🔄 *Report Returned Products (Optional)*\n\n"
        "Do you have any damaged or incorrect items to return?\n"
        "• Type the description (e.g. `Tomato 5 KG – damaged`)\n"
        "• Or send a *photo / proof* directly (with optional caption)\n\n"
        "Tap ⏭ *Skip Returns* if you have no returns."
    )


from utils.helpers import safe_edit_text_or_caption

@router.message(F.text.in_({"💬 Feedback", "💬 አስተያየት", "💬 Yaada"}))
async def start_direct_feedback(message: Message, state: FSMContext, session: AsyncSession):
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(message.from_user.id)
    user_lang = getattr(customer, "language", "en") or "en"

    await state.set_state(OrderState.waiting_for_direct_feedback)
    await message.answer(
        t("feedback_prompt", user_lang),
        parse_mode="Markdown",
    )

@router.message(OrderState.waiting_for_direct_feedback, F.text)
async def submit_direct_feedback(message: Message, state: FSMContext, session: AsyncSession):
    feedback_text = (message.text or "").strip()
    if not feedback_text:
        await message.answer("❌ Please enter your feedback text.")
        return

    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(message.from_user.id)
    user_lang = getattr(customer, "language", "en") or "en"

    await state.clear()
    await notify_quality_control(
        message.bot,
        order=None,
        rating=None,
        feedback=feedback_text,
        returned_items=None,
        photo_file_id=None,
        customer=customer,
    )

    last = await OrderRepository(session).get_last_order(customer.id) if customer else None
    menu = customer_reorder_menu(user_lang) if last else customer_menu(user_lang)
    await message.answer(
        t("feedback_submitted", user_lang),
        reply_markup=menu,
        parse_mode="Markdown",
    )

@router.callback_query(F.data.startswith("rate_order:"))
async def receive_rating(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    parts = callback.data.split(":") # type: ignore
    if len(parts) != 3:
        await callback.answer("Invalid rating.", show_alert=True)
        return

    order_id = int(parts[1])
    rating = int(parts[2])
    if rating < 1 or rating > 5:
        await callback.answer("Rating must be 1–5.", show_alert=True)
        return

    repo = OrderRepository(session)
    user_repo = UserRepository(session)

    order = await repo.get_order(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return
    if order.status != OrderStatus.DELIVERED:
        await callback.answer("Rating is only available for delivered orders.", show_alert=True)
        return

    me = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not me or order.customer_id != me.id:
        await callback.answer("⚠️ You can only rate your own orders.", show_alert=True)
        return

    await callback.answer()
    await state.update_data(
        rating_order_id=order_id,
        rating_value=rating
    )
    await state.set_state(OrderState.waiting_for_feedback)

    stars_filled = "⭐" * rating
    stars_empty = "☆" * (5 - rating)

    await safe_edit_text_or_caption(
        callback,
        f"✅ Thank you for your rating!\n\n"
        f"{stars_filled}{stars_empty}  {rating}/5\n\n"
        "Would you like to leave a short feedback?\n"
        "_(Type your message or tap Skip.)_",
        reply_markup=_skip_feedback_keyboard(),
        parse_mode="Markdown",
    )

@router.message(OrderState.waiting_for_feedback)
async def receive_feedback(message: Message, state: FSMContext):
    feedback_text = message.text.strip() if message.text else None
    await state.update_data(rating_feedback=feedback_text)
    
    await state.set_state(OrderState.waiting_for_returns_post_feedback)
    await message.answer(
        _returns_prompt(),
        reply_markup=_skip_returns_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "rating_skip_feedback")
async def skip_feedback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(rating_feedback=None)
    
    await state.set_state(OrderState.waiting_for_returns_post_feedback)
    await safe_edit_text_or_caption(
        callback,
        _returns_prompt(),
        reply_markup=_skip_returns_keyboard(),
        parse_mode="Markdown"
    )

@router.message(OrderState.waiting_for_returns_post_feedback, F.text)
async def receive_returns_text(message: Message, state: FSMContext):
    """Handle text-only returns description and ask for photo/proof."""
    returns_text = message.text.strip() if message.text else None
    if not returns_text:
        await message.answer(
            "❌ Please describe the returned items or send a photo proof. Tap ⏭ Skip Returns to skip.",
            reply_markup=_skip_returns_keyboard(),
            parse_mode="Markdown",
        )
        return
    await state.update_data(rating_returns_text=returns_text)
    await state.set_state(OrderState.waiting_for_return_photo)
    await message.answer(
        "📷 *Please send a photo or proof of the returned items:*\n\n"
        "_(Send a photo now, or tap ⏭ Skip Photo to submit without a photo)_",
        reply_markup=_skip_photo_keyboard(),
        parse_mode="Markdown",
    )


@router.message(OrderState.waiting_for_returns_post_feedback, F.photo)
async def receive_returns_photo_direct(message: Message, state: FSMContext, session: AsyncSession):
    """Handle photo (with optional caption) as direct returns report."""
    photo_file_id = message.photo[-1].file_id  # highest resolution
    returns_text = message.caption.strip() if message.caption else "Photo proof submitted"
    await _save_rating_and_returns(message, state, session, returns_text=returns_text, photo_file_id=photo_file_id)


@router.message(OrderState.waiting_for_return_photo, F.photo)
async def receive_returns_proof_photo(message: Message, state: FSMContext, session: AsyncSession):
    """Handle proof photo after description entered."""
    photo_file_id = message.photo[-1].file_id
    data = await state.get_data()
    returns_text = data.get("rating_returns_text") or (message.caption.strip() if message.caption else "Photo proof submitted")
    await _save_rating_and_returns(message, state, session, returns_text=returns_text, photo_file_id=photo_file_id)


@router.callback_query(OrderState.waiting_for_return_photo, F.data == "rating_skip_photo")
async def skip_returns_photo(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Handle skipping photo proof."""
    await callback.answer()
    data = await state.get_data()
    returns_text = data.get("rating_returns_text")
    await _save_rating_and_returns(callback.message, state, session, returns_text=returns_text, photo_file_id=None, telegram_id=callback.from_user.id) # type: ignore


async def _save_rating_and_returns(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    returns_text: str | None,
    photo_file_id: str | None,
    telegram_id: int | None = None,
):
    data = await state.get_data()
    order_id = data.get("rating_order_id")
    rating   = data.get("rating_value")
    feedback = data.get("rating_feedback")
    await state.clear()

    repo = OrderRepository(session)
    order = await repo.get_order(order_id) # type: ignore
    if not order:
        await message.answer("❌ Order not found.")
        return

    order.rating   = rating
    order.feedback = feedback
    order.returns  = returns_text
    await repo.add(order)

    # Directly forward full Quality Control Report to QC group & admins
    await notify_quality_control(
        message.bot, # type: ignore
        order,
        rating=rating,
        feedback=feedback,
        returned_items=returns_text,
        photo_file_id=photo_file_id,
    )

    if returns_text or photo_file_id:
        await notify_sales_managers(message.bot, order, "Returned") # type: ignore

    tid = telegram_id or (message.from_user.id if message.from_user else message.chat.id)
    user_repo = UserRepository(session)
    customer  = await user_repo.get_by_telegram_id(tid)
    user_lang = getattr(customer, "language", "en") or "en"
    role_val = customer.role.value if customer and hasattr(customer.role, "value") else (str(customer.role) if customer else "")
    if role_val in ("hotel_admin", "hotel"):
        from keyboards.store_manager import hotel_admin_menu
        menu = hotel_admin_menu(user_lang)
    elif role_val == "store_manager":
        from keyboards.store_manager import store_manager_menu
        menu = store_manager_menu(user_lang)
    else:
        last = await repo.get_last_order(customer.id) if customer else None
        menu = customer_reorder_menu(user_lang) if last else customer_menu(user_lang)

    await message.answer(
        "✅ *Review & Quality Report Submitted!*\n\n"
        "Thank you! Your rating, feedback, and return details have been directly forwarded to our Quality Control team.",
        reply_markup=menu,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "rating_skip_returns")
async def skip_returns(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    data = await state.get_data()
    order_id = data.get("rating_order_id")
    rating   = data.get("rating_value")
    feedback = data.get("rating_feedback")
    await state.clear()

    repo = OrderRepository(session)
    order = await repo.get_order(order_id) # type: ignore
    if not order:
        await callback.message.answer("❌ Order not found.") # type: ignore
        return

    order.rating   = rating
    order.feedback = feedback
    order.returns  = None
    await repo.add(order)

    # Directly forward rating & feedback to QC
    await notify_quality_control(
        callback.bot,
        order,
        rating=rating,
        feedback=feedback,
        returned_items=None,
        photo_file_id=None,
    )

    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    user_lang = getattr(customer, "language", "en") or "en"
    role_val = customer.role.value if customer and hasattr(customer.role, "value") else (str(customer.role) if customer else "")
    if role_val in ("hotel_admin", "hotel"):
        from keyboards.store_manager import hotel_admin_menu
        menu = hotel_admin_menu(user_lang)
    elif role_val == "store_manager":
        from keyboards.store_manager import store_manager_menu
        menu = store_manager_menu(user_lang)
    else:
        last = await repo.get_last_order(customer.id) if customer else None
        menu = customer_reorder_menu(user_lang) if last else customer_menu(user_lang)

    await callback.message.edit_text( # type: ignore
        "✅ *Order Review Submitted!*\n\n"
        "Thank you! Your ratings and feedback have been submitted successfully.",
        parse_mode="Markdown"
    )
    await callback.message.answer("Choose an option:", reply_markup=menu) # type: ignore
