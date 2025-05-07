from aiogram.fsm.state import State, StatesGroup


class FSMUser(StatesGroup):
    music_list = State()


class FSMAdmin(StatesGroup):
    # Song creation
    enter_title = State()
    select_type = State()
    select_tempo = State()
    enter_genres = State()
    enter_lyrics = State()
    upload_video = State()
    confirm_data = State()
    # Song deletion
    enter_delete_title = State()
    # User history
    enter_username = State()


__all__ = ["FSMUser"]
