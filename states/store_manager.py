from aiogram.fsm.state import State, StatesGroup
class StoreManagerState(StatesGroup):
    waiting_for_driver_name  = State()
    waiting_for_reject_reason = State()
    waiting_for_message_text = State()
