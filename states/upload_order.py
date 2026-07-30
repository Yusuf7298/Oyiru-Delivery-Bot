from aiogram.fsm.state import State, StatesGroup
class UploadOrderState(StatesGroup):
    waiting_for_file = State()
