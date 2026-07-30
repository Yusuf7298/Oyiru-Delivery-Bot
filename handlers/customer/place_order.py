from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from keyboards.customer.order import order_method_keyboard
from filters.role_filter import RoleFilter

router = Router()
router.message.filter(RoleFilter(["customer"]))

@router.message(F.text == "📦 Place Order")
async def place_order_entry(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    await message.answer(
        "🛒 How would you like to place your order?\n\n"
        "   🧺 Listing Order — Select categories and type quantities\n"
        "   📄 Upload Photo — Send a photo or file of your product list",
        reply_markup=order_method_keyboard(),
        parse_mode="Markdown",
    )