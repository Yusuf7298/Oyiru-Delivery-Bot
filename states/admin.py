from aiogram.fsm.state import State, StatesGroup
class HotelStates(StatesGroup):
    waiting_name = State()
    waiting_address = State()
    waiting_phone = State()
    # edit
    editing_name = State()
    editing_address = State()
    editing_phone = State()


class CategoryStates(StatesGroup):
    waiting_name = State()
    editing_name = State()


class ProductStates(StatesGroup):
    waiting_name = State()
    waiting_unit = State()
    waiting_category = State()
    waiting_batch = State()   # bulk add: "Name - unit\nName2 - unit2"
    # edit
    editing_name = State()
    editing_unit = State()
    editing_category = State()

