from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.user_repository import UserRepository
from services.auth_service import AuthService
from states.registration import RegistrationState

router = Router()

@router.callback_query(F.data.startswith("hotel:"))
async def hotel_selected(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    hotel_id = int(callback.data.split(":")[1]) # type: ignore
    user_repo = UserRepository(session)
    auth = AuthService(user_repo)
    user = await auth.user_exists(callback.from_user.id)

    if user is not None:
        # Already registered — do not allow hotel re-selection
        await callback.message.edit_text( # type: ignore
            "✅ You are already registered.\nUse /start to access your menu."
        )
        await callback.answer()
        return

    # Determine if hotel already has a registered hotel admin
    claimed_ids = await user_repo.get_claimed_hotel_ids()
    is_admin = (hotel_id not in claimed_ids)

    from database.repositories.hotel_repository import HotelRepository
    hotel = await HotelRepository(session).get_by_id(hotel_id)
    hotel_name = hotel.name if hotel else "Hotel"

    await state.update_data(hotel_id=hotel_id, is_hotel_admin=is_admin, is_staff_invite=False)
    await callback.message.edit_text( # type: ignore
        f"🏨 *{hotel_name}* selected.\n\n"
        "Please enter your *full name* to complete registration:",
        parse_mode="Markdown",
    )
    await state.set_state(RegistrationState.full_name)
    await callback.answer()
