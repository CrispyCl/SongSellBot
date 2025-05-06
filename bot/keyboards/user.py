from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


class MainUserKeyboard:
    def __call__(self, is_admin: bool) -> ReplyKeyboardMarkup:
        buttons: list[list[KeyboardButton]] = [
            [KeyboardButton(text="✨ Песни")],
        ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


__all__ = ["MainUserKeyboard"]
