#from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class WebRename(StatesGroup):
    new_forename = State()
    new_emoji = State()

class WebTransferOwnership(StatesGroup):
    new_tid_owner = State()
