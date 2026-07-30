from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from filters.role_filter import RoleFilter
from keyboards.admin_menu import admin_main_menu

router = Router()
router.message.filter(RoleFilter(["admin"]))

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    await message.answer(
        "👑 *Admin Panel*\n\nChoose a section:",
        reply_markup=admin_main_menu(),
        parse_mode="Markdown",
    )
