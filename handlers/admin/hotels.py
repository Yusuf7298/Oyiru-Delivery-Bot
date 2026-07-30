from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.hotel import Hotel
from database.repositories.hotel_repository import HotelRepository
from filters.role_filter import RoleFilter
from keyboards.admin_menu import (
    hotel_list_keyboard,
    hotel_detail_keyboard,
    confirm_delete_keyboard,
    admin_main_menu,
)
from states.admin import HotelStates

router = Router()
router.message.filter(RoleFilter(["admin"]))
router.callback_query.filter(RoleFilter(["admin"]))


@router.message(F.text == "🏨 Hotels")
async def hotels_menu(message: Message, session: AsyncSession):
    repo = HotelRepository(session)
    hotels = await repo.get_all()
    if not hotels:
        await message.answer(
            "No hotels yet.\nTap *➕ Add Hotel* to create the first one.",
            reply_markup=hotel_list_keyboard([]),
            parse_mode="Markdown",
        )
        return
    await message.answer(
        f"🏨 *Hotels* ({len(hotels)} total)\n\n✅ = Active  ❌ = Inactive",
        reply_markup=hotel_list_keyboard(hotels),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "admin_hotels_back")
async def hotels_back(callback: CallbackQuery, session: AsyncSession):
    repo = HotelRepository(session)
    hotels = await repo.get_all()
    await callback.message.edit_text( # type: ignore
        f"🏨 *Hotels* ({len(hotels)} total)\n\n✅ = Active  ❌ = Inactive",
        reply_markup=hotel_list_keyboard(hotels),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_hotel:"))
async def hotel_detail(callback: CallbackQuery, session: AsyncSession):
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    repo = HotelRepository(session)
    hotel = await repo.get_by_id(hotel_id)
    if not hotel:
        await callback.answer("Hotel not found.", show_alert=True)
        return
    status = "✅ Active" if hotel.is_active else "❌ Inactive"
    text = (
        f"🏨 *{hotel.name}*\n\n"
        f"📍 Address: {hotel.address or '—'}\n"
        f"📞 Phone: {hotel.phone or '—'}\n"
        f"Status: {status}"
    )
    await callback.message.edit_text( # type: ignore
        text, reply_markup=hotel_detail_keyboard(hotel), parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_hotel_add")
async def hotel_add_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🏨 Enter the *hotel name*:", parse_mode="Markdown") # type: ignore
    await state.set_state(HotelStates.waiting_name)
    await callback.answer()


@router.message(HotelStates.waiting_name)
async def hotel_add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip()) # type: ignore
    await message.answer("📍 Enter the *address* (or send — to skip):", parse_mode="Markdown")
    await state.set_state(HotelStates.waiting_address)


@router.message(HotelStates.waiting_address)
async def hotel_add_address(message: Message, state: FSMContext):
    val = message.text.strip() # type: ignore
    await state.update_data(address=None if val == "—" else val)
    await message.answer("📞 Enter the *phone* (or send — to skip):", parse_mode="Markdown")
    await state.set_state(HotelStates.waiting_phone)


@router.message(HotelStates.waiting_phone)
async def hotel_add_phone(message: Message, state: FSMContext, session: AsyncSession):
    val = message.text.strip() # type: ignore
    data = await state.get_data()
    await state.clear()

    repo = HotelRepository(session)
    existing = await repo.get_by_name(data["name"])
    if existing:
        await message.answer(f"❌ A hotel named *{data['name']}* already exists.", parse_mode="Markdown")
        return

    hotel = Hotel(
        name=data["name"],
        address=data.get("address"),
        phone=None if val == "—" else val,
    )
    await repo.create(hotel)
    await message.answer(
        f"✅ Hotel *{hotel.name}* created successfully.",
        reply_markup=admin_main_menu(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("admin_hotel_edit_name:"))
async def hotel_edit_name_start(callback: CallbackQuery, state: FSMContext):
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    await state.update_data(hotel_id=hotel_id)
    await callback.message.answer("✏️ Enter the *new hotel name*:", parse_mode="Markdown") # type: ignore
    await state.set_state(HotelStates.editing_name)
    await callback.answer()


@router.message(HotelStates.editing_name)
async def hotel_edit_name_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()
    repo = HotelRepository(session)
    hotel = await repo.get_by_id(data["hotel_id"])
    if not hotel:
        await message.answer("❌ Hotel not found.")
        return
    existing = await repo.get_by_name(message.text.strip()) # type: ignore
    if existing and existing.id != hotel.id:
        await message.answer(f"❌ Name *{message.text.strip()}* is already taken.", parse_mode="Markdown") # type: ignore
        return
    hotel.name = message.text.strip() # type: ignore
    await repo.update(hotel)
    await message.answer(f"✅ Hotel name updated to *{hotel.name}*.", parse_mode="Markdown")


@router.callback_query(F.data.startswith("admin_hotel_edit_addr:"))
async def hotel_edit_addr_start(callback: CallbackQuery, state: FSMContext):
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    await state.update_data(hotel_id=hotel_id)
    await callback.message.answer("📍 Enter the *new address* (or — to clear):", parse_mode="Markdown") # type: ignore
    await state.set_state(HotelStates.editing_address)
    await callback.answer()


@router.message(HotelStates.editing_address)
async def hotel_edit_addr_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()
    repo = HotelRepository(session)
    hotel = await repo.get_by_id(data["hotel_id"])
    if not hotel:
        await message.answer("❌ Hotel not found.")
        return
    hotel.address = None if message.text.strip() == "—" else message.text.strip() # type: ignore
    await repo.update(hotel)
    await message.answer("✅ Address updated.")


@router.callback_query(F.data.startswith("admin_hotel_edit_phone:"))
async def hotel_edit_phone_start(callback: CallbackQuery, state: FSMContext):
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    await state.update_data(hotel_id=hotel_id)
    await callback.message.answer("📞 Enter the *new phone* (or — to clear):", parse_mode="Markdown") # type: ignore
    await state.set_state(HotelStates.editing_phone)
    await callback.answer()


@router.message(HotelStates.editing_phone)
async def hotel_edit_phone_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()
    repo = HotelRepository(session)
    hotel = await repo.get_by_id(data["hotel_id"])
    if not hotel:
        await message.answer("❌ Hotel not found.")
        return
    hotel.phone = None if message.text.strip() == "—" else message.text.strip() # type: ignore
    await repo.update(hotel)
    await message.answer("✅ Phone updated.")


@router.callback_query(F.data.startswith("admin_hotel_deactivate:"))
async def hotel_deactivate(callback: CallbackQuery, session: AsyncSession):
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    repo = HotelRepository(session)
    hotel = await repo.get_by_id(hotel_id)
    if not hotel:
        await callback.answer("Hotel not found.", show_alert=True)
        return
    await repo.soft_delete(hotel)
    await callback.answer("🔴 Hotel deactivated.", show_alert=True)
    # Refresh detail view
    status = "✅ Active" if hotel.is_active else "❌ Inactive"
    await callback.message.edit_text( # type: ignore
        f"🏨 *{hotel.name}*\n\n📍 {hotel.address or '—'}\n📞 {hotel.phone or '—'}\nStatus: {status}",
        reply_markup=hotel_detail_keyboard(hotel),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("admin_hotel_activate:"))
async def hotel_activate(callback: CallbackQuery, session: AsyncSession):
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    repo = HotelRepository(session)
    hotel = await repo.get_by_id(hotel_id)
    if not hotel:
        await callback.answer("Hotel not found.", show_alert=True)
        return
    await repo.activate(hotel)
    await callback.answer("🟢 Hotel activated.", show_alert=True)
    status = "✅ Active" if hotel.is_active else "❌ Inactive"
    await callback.message.edit_text( # type: ignore
        f"🏨 *{hotel.name}*\n\n📍 {hotel.address or '—'}\n📞 {hotel.phone or '—'}\nStatus: {status}",
        reply_markup=hotel_detail_keyboard(hotel),
        parse_mode="Markdown",
    )

@router.callback_query(F.data.startswith("admin_hotel_delete:"))
async def hotel_delete_confirm(callback: CallbackQuery, session: AsyncSession):
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    repo = HotelRepository(session)
    hotel = await repo.get_by_id(hotel_id)
    if not hotel:
        await callback.answer("Hotel not found.", show_alert=True)
        return
    await callback.message.edit_text( # type: ignore
        f"⚠️ Are you sure you want to *delete* hotel *{hotel.name}*?\n"
        "This will soft-delete it (deactivate). All historical orders are preserved.",
        reply_markup=confirm_delete_keyboard("hotel", hotel_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_hotel:"))
async def hotel_delete_execute(callback: CallbackQuery, session: AsyncSession):
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    repo = HotelRepository(session)
    hotel = await repo.get_by_id(hotel_id)
    if not hotel:
        await callback.answer("Hotel not found.", show_alert=True)
        return
    await repo.soft_delete(hotel)
    hotels = await repo.get_all()
    await callback.message.edit_text( # type: ignore
        f"🗑 Hotel *{hotel.name}* deleted (deactivated).\n\n"
        f"🏨 *Hotels* ({len(hotels)} total)\n✅ = Active  ❌ = Inactive",
        reply_markup=hotel_list_keyboard(hotels),
        parse_mode="Markdown",
    )
    await callback.answer("Deleted.")


@router.callback_query(F.data.startswith("cancel_delete_hotel:"))
async def hotel_delete_cancel(callback: CallbackQuery, session: AsyncSession):
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    repo = HotelRepository(session)
    hotel = await repo.get_by_id(hotel_id)
    if not hotel:
        await callback.answer()
        return
    status = "✅ Active" if hotel.is_active else "❌ Inactive"
    await callback.message.edit_text( # type: ignore
        f"🏨 *{hotel.name}*\n\n📍 {hotel.address or '—'}\n📞 {hotel.phone or '—'}\nStatus: {status}",
        reply_markup=hotel_detail_keyboard(hotel),
        parse_mode="Markdown",
    )
    await callback.answer("Cancelled.")
