from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


class MainUserKeyboard:
    def __call__(self, is_admin: bool) -> ReplyKeyboardMarkup:
        buttons: list[list[KeyboardButton]] = [
            [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="🛒 Корзина")],
        ]
        if is_admin:
            buttons.append([KeyboardButton(text="🔐 Панель администратора")])
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


class CancelKeyboard:
    def __call__(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отменить")]],
            resize_keyboard=True,
        )


__all__ = ["MainUserKeyboard", "CancelKeyboard"]
