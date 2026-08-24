from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.user_repository import UserRepository
from services.auth_service import AuthService
from keyboards.customers import customer_menu
from keyboards.hotel import hotel_menu
from states.registration import RegistrationState

router = Router()
@router.message(CommandStart())
async def start(message: Message,state,session: AsyncSession,):
    user_repo = UserRepository(session)
    auth = AuthService(user_repo)
    user = await auth.user_exists(message.from_user.id) # type: ignore
    if not user:
        await message.answer("You are not registered.")
        return
    if user.role == "customer":
        await message.answer(
            f"Welcome back {user.full_name}!",
            reply_markup=customer_menu(),
        )
        return
    elif user.role == "hotel":
        await message.answer(
            f"Welcome {user.full_name}",
            reply_markup=hotel_menu(),
        )
    elif user.role == "admin":
        await message.answer(
            f"Welcome Admin {user.full_name}",
        )
    
    else:
        await message.answer(
            "👋 Welcome to Oyirubot.\n\n"
            "Let's create your account.\n\n"
            "Enter your full name:"
        )
        await state.set_state(
            RegistrationState.full_name)