from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.user_repository import UserRepository
from database.repositories.order_repository import OrderRepository
from database.models.user import UserRole
from keyboards.customers import customer_menu, customer_reorder_menu
from keyboards.store_manager import store_manager_menu
from keyboards.delivery import delivery_menu
from keyboards.admin_menu import admin_main_menu

router = Router()


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    current = await state.get_state()
    await state.clear()

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id) # type: ignore
    if not user:
        await message.answer("❌ Operation cancelled.")
        return

    if user.role == UserRole.CUSTOMER:
        order_repo = OrderRepository(session)
        last = await order_repo.get_last_order(user.id)
        menu = customer_reorder_menu() if last else customer_menu()
        await message.answer(
            "❌ Cancelled." if current else "ℹ️ Nothing to cancel.",
            reply_markup=menu,
        )
    elif user.role == UserRole.HOTEL:
        await message.answer(
            "❌ Cancelled." if current else "ℹ️ Nothing to cancel.",
            reply_markup=store_manager_menu(),
        )
    elif user.role == UserRole.DELIVERY:
        await message.answer(
            "❌ Cancelled." if current else "ℹ️ Nothing to cancel.",
            reply_markup=delivery_menu(),
        )
    elif user.role == UserRole.ADMIN:
        await message.answer(
            "❌ Cancelled." if current else "ℹ️ Nothing to cancel.",
            reply_markup=admin_main_menu(),
        )
    else:
        await message.answer("❌ Cancelled.")
