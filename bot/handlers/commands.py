from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards import MainUserKeyboard
from models import User

router = Router()


@router.message(CommandStart())
@router.message(F.text == "🏠 На главную")
async def process_start_command(message: Message, state: FSMContext, current_user: User) -> None:
    await state.clear()

    welcome_text = (
        "👋 <b>Добро пожаловать в музыкального бота!</b>\n\n"
        "🎶 Этот бот создан для удобной покупки и прослушивания песен.\n\n"
        "🔍 <b>Доступные команды:</b>\n"
        "• /start - Перезапустить бота\n"
        "• /help - Инструкция по использованию\n"
        "• /search - Поиск песен\n"
        "• /wishlist - Ваша корзина\n\n"
        "💡 Начните с поиска интересующих вас песен!"
    )

    keyboard = MainUserKeyboard()(current_user.is_staff)
    await message.answer(welcome_text, reply_markup=keyboard)


@router.message(Command("help"))
async def process_help_command(message: Message, current_user: User) -> None:
    help_text = (
        "ℹ️ <b>Справка по использованию бота</b>\n\n"
        "🎵 <b>Основные функции:</b>\n"
        "• Поиск песен по названию, жанру и темпу\n"
        "• Прослушивание демо-версий\n"
        "• Добавление в список желаний\n"
        "• Покупка полных версий\n\n"
        "🛒 <b>Как купить песню:</b>\n"
        "1. Найдите песню через поиск\n"
        "2. Добавьте песню в избранное\n"
        "3. Мы свяжемся с вами для обсуждения покупки!\n\n"
        "📌 <b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/search - Поиск песен\n"
        "/wishlist - Ваша корзина"
    )

    keyboard = MainUserKeyboard()(current_user.is_staff)
    await message.answer(help_text, reply_markup=keyboard)


__all__ = ["router"]
