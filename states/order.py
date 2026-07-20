from aiogram.fsm.state import State, StatesGroup
class PlaceOrderState(StatesGroup):
    selecting_categories = State()
    entering_category_quantities = State()
    order_summary = State()