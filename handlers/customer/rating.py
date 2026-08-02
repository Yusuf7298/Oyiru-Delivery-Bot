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

router = Router()
router.message.filter(RoleFilter(["customer"]))
router.callback_query.filter(RoleFilter(["customer"]))

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


def _returns_prompt() -> str:
    return (
        "🔄 Report Returned Products\n\n"
        "Do you have any items to return for this order?\n"
        "• Type a description (e.g. `Tomato - 5 KG, Reason: Damaged`)\n"
        "• Or send a *photo* of the returned items (optionally add a caption)\n\n"
        "Tap ⏭ Skip Returns to continue without reporting."
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

    await callback.message.edit_text( # type: ignore
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
    await callback.message.edit_text( # type: ignore
        _returns_prompt(),
        reply_markup=_skip_returns_keyboard(),
        parse_mode="Markdown"
    )

@router.message(OrderState.waiting_for_returns_post_feedback)
async def receive_returns(message: Message, state: FSMContext, session: AsyncSession):
    """Handle text-only returns description."""
    returns_text = message.text.strip() if message.text else None
    if not returns_text:
        await message.answer(
            "❌ Please describe the returned items or send a photo. Tap ⏭ Skip Returns to skip.",
            reply_markup=_skip_returns_keyboard(),
            parse_mode="Markdown",
        )
        return
    await _save_rating_and_returns(message, state, session, returns_text=returns_text, photo_file_id=None)


@router.message(OrderState.waiting_for_returns_post_feedback, F.photo)
async def receive_returns_photo(message: Message, state: FSMContext, session: AsyncSession):
    """Handle photo (with optional caption) as returns report."""
    photo_file_id = message.photo[-1].file_id  # highest resolution
    returns_text = message.caption.strip() if message.caption else "Photo submitted"
    await _save_rating_and_returns(message, state, session, returns_text=returns_text, photo_file_id=photo_file_id)


async def _save_rating_and_returns(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    returns_text: str | None,
    photo_file_id: str | None,
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
    await session.commit()

    await notify_quality_control(message.bot, order, rating, feedback, returns_text) # type: ignore

    if returns_text or photo_file_id:
        from services.notification_service import notify_returned_products
        await notify_returned_products(message.bot, order, returns_text or "See photo", photo_file_id=photo_file_id) # type: ignore
        await notify_sales_managers(message.bot, order, "Returned") # type: ignore

    user_repo = UserRepository(session)
    customer  = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    last      = await repo.get_last_order(customer.id) if customer else None
    menu      = customer_reorder_menu() if last else customer_menu()
    await message.answer(
        "✅ Order Review Submitted!\n\n"
        "Thank you! Your ratings, feedback, and return logs have been submitted successfully.",
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
    await session.commit()
    await notify_quality_control(callback.bot, order, rating, feedback, None) # type: ignore

    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    last = await repo.get_last_order(customer.id) if customer else None
    menu = customer_reorder_menu() if last else customer_menu()

    await callback.message.edit_text( # type: ignore
        "✅ Order Review Submitted!\n\n"
        "Thank you! Your ratings and feedback have been submitted successfully.",
        parse_mode="Markdown"
    )
    await callback.message.answer("Choose an option:", reply_markup=menu) # type: ignore
