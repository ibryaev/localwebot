#from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class WebRename(StatesGroup):
    new_forename = State()
    new_emoji = State()

class WebTransferOwnership(StatesGroup):
    new_tid_owner = State()

admin_type_str = {
    "owner": "Владелец",
    "helper": "Хелпер",
    "admin": "Админ",
    "moder": "Модер"
}
admin_type_int = {
    4: "owner",
    3: "helper",
    2: "admin",
    1: "moder"
}
