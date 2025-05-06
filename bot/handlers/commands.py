from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards import MainUserKeyboard
from models import User

router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext, current_user: User) -> None:
    await state.clear()

    welcome_text = (
        "Приветствую✌️\n\n"
        "🤖 Этот бот создан для удобной покупки песен.\n\n"
        "📌 Доступные команды:\n"
        "/help - Инструкция по использованию бота\n"
    )

    keyboard = MainUserKeyboard()(current_user.is_staff)

    await message.answer(welcome_text, reply_markup=keyboard)


__all__ = ["router"]
