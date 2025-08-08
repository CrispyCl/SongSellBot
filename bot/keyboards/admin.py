from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


class AdminPanelKeyboard:
    def __call__(self) -> ReplyKeyboardMarkup:
        buttons: list[list[KeyboardButton]] = [
            [KeyboardButton(text="🏠 На главную")],
            [
                KeyboardButton(text="🎵 Добавить песню"),
                KeyboardButton(text="✏️ Изменить песню"),
                KeyboardButton(text="🗑 Удалить песню"),
            ],
            [KeyboardButton(text="📜 История пользователя")],
        ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


class AcceptCancelKeyboard:
    def __call__(self) -> ReplyKeyboardMarkup:
        buttons: list[list[KeyboardButton]] = [
            [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отменить")],
        ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


class EditionCancelKeyboart:
    def __call__(self) -> InlineKeyboardMarkup:
        buttons: list[list[InlineKeyboardButton]] = [
            [InlineKeyboardButton(text="❌ Отменить", callback_data="edit_cancel")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)


__all__ = ["AdminPanelKeyboard", "AcceptCancelKeyboard", "EditionCancelKeyboart"]
