from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_role = State()
    waiting_for_region = State()
    waiting_for_district = State()
    waiting_for_school = State()
