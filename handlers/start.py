from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.user_repository import UserRepository
from services.auth_service import AuthService
from keyboards.customers import customer_menu
from keyboards.hotel import hotel_menu
from states.registration import RegistrationState
from keyboards.delivery import delivery_menu

router = Router()
@router.message(CommandStart())
async def start(message: Message, state: FSMContext, session: AsyncSession,):
    user_repo = UserRepository(session)
    auth = AuthService(user_repo)
    user = await auth.user_exists(message.from_user.id) # type: ignore
    if not user:
        await message.answer(
            "👋 Welcome to Oyiru Delivery.\n\n"
            "Let's create your account.\n\n"
            "Enter your full name:"
        )
        await state.set_state(RegistrationState.full_name)
        return

    if user.role == "customer":
        await message.answer(
            f"Welcome back {user.full_name}!",
            reply_markup=customer_menu(),
        )

    elif user.role == "hotel":
        await message.answer(
            f"Welcome {user.full_name}!",
            reply_markup=hotel_menu(),
        )

    elif user.role == "admin":
        await message.answer(
            f"Welcome Admin {user.full_name}!",
        )

    elif user.role == "delivery_partner":
        await message.answer(
            f"Welcome {user.full_name}!",
            reply_markup=delivery_menu(),)