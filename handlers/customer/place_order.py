from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from keyboards.customer.order import order_method_keyboard
from filters.role_filter import RoleFilter
from utils.i18n import t

router = Router()
router.message.filter(RoleFilter(["customer"]))

PLACE_ORDER_BUTTONS = ["🛒 Place Order", "🛒 ትዕዛዝ ያስገቡ", "🛒 Ajaja Galchuu"]

@router.message(F.text.in_(PLACE_ORDER_BUTTONS))
async def place_order_entry(message: Message, state: FSMContext, session: AsyncSession, lang: str = "en"):
    await state.clear()
    await message.answer(
        t("order_title", lang),
        reply_markup=order_method_keyboard(lang),
        parse_mode="Markdown",
    )

