from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


class AdminPanelKeyboard:
    def __call__(self) -> ReplyKeyboardMarkup:
        buttons: list[list[KeyboardButton]] = [
            [KeyboardButton(text="🏠 На главную")],
            [KeyboardButton(text="🎵 Добавить песню"), KeyboardButton(text="📜 История пользователя")],
        ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


class AcceptCancelKeyboard:
    def __call__(self) -> ReplyKeyboardMarkup:
        buttons: list[list[KeyboardButton]] = [
            [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отменить")],
        ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


__all__ = ["AdminPanelKeyboard", "AcceptCancelKeyboard"]
