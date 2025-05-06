from aiogram.fsm.state import State, StatesGroup


class FSMUser(StatesGroup):
    start_menu = State()


__all__ = ["FSMUser"]
