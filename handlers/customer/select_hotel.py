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

    # New user claiming unclaimed hotel — store hotel and mark as Hotel Admin
    await state.update_data(hotel_id=hotel_id, is_hotel_admin=True, is_staff_invite=False)
    await callback.message.edit_text( # type: ignore
        "✅ Hotel selected.\n\nPlease enter your *full name* to complete your Hotel Administrator registration:",
        parse_mode="Markdown",
    )
    await state.set_state(RegistrationState.full_name)
    await callback.answer()
