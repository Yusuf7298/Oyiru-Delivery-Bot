from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.hotel import hotel_menu
from services.auth_service import AuthService
router = Router()
@router.message(CommandStart())
async def hotel_start(message: Message, auth: AuthService):
    user = await auth.user_exists(message.from_user.id) # type: ignore
    if not user:
        return
    if user.role != "hotel":
        return
    await message.answer(f"Welcome {user.full_name}",reply_markup=hotel_menu(),)