from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.hotel_repository import HotelRepository
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from states.registration import RegistrationState
from database.repositories.user_repository import UserRepository
from services.auth_service import AuthService
from keyboards.customers import customer_menu
router = Router()
@router.message(RegistrationState.full_name)
async def full_name(message: Message,state: FSMContext,):
    await state.update_data(full_name=message.text)
    await message.answer("Enter your phone number:")
    await state.set_state(RegistrationState.phone)

@router.message(RegistrationState.phone)
async def phone(message: Message,state: FSMContext,session: AsyncSession,):
    await state.update_data(phone=message.text)
    hotels = await HotelRepository(session).get_active_hotels()
    keyboard = []
    for hotel in hotels:
        keyboard.append(
            [KeyboardButton(text=hotel.name)])
    await message.answer(
        "Select your hotel:",

        reply_markup=ReplyKeyboardMarkup(

            keyboard=keyboard,

            resize_keyboard=True,

        ),

    )

    await state.set_state(

        RegistrationState.hotel

    )
@router.message(RegistrationState.hotel)
async def hotel_selected(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):

    hotel_repo = HotelRepository(session)

    hotel = await hotel_repo.get_by_name(message.text) # type: ignore

    if hotel is None:

        hotels = await hotel_repo.get_active_hotels()

        keyboard = [
            [KeyboardButton(text=h.name)]
            for h in hotels
        ]

        await message.answer(

            "❌ Please choose a hotel from the list.",

            reply_markup=ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True
            )

        )

        return

    data = await state.get_data()

    user_repo = UserRepository(session)

    auth = AuthService(user_repo)

    await auth.register_user(

        telegram_id=message.from_user.id, # type: ignore

        full_name=data["full_name"],

        username=message.from_user.username, # type: ignore

        phone=data["phone"],

        hotel_id=hotel.id,

    )

    await state.clear()

    await message.answer(

        f"✅ Registration completed successfully!\n\n"
        f"Welcome, {data['full_name']}!",

        reply_markup=customer_menu()

    )