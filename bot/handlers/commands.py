from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import MainUserKeyboard
from models import User

router = Router()


@router.callback_query(F.data == "to_main")
async def to_main_menu(callback: CallbackQuery, state: FSMContext, current_user: User):
    await state.clear()
    await process_start_command(callback.message, state, current_user=current_user)
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.message(CommandStart())
@router.message(F.text == "🏠 На главную")
async def process_start_command(message: Message, state: FSMContext, current_user: User) -> None:
    await state.clear()

    welcome_text = (
        "👋 Добро пожаловать в музыкальный бот Иры Эйфории🤖\n"
        "Я автора сотни хитов для Топовых артистов в нашей стране!\n\n"
        "🎶 Этот бот создан для удобного прослушивания песен и их покупки в один клик.\n\n"
        "Жми «Каталог песен» 👇 и выбирай лучшую для себя"
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
        "1. Найдите песню в каталоге\n"
        "2. Добавьте песню в избранное\n"
        "3. Мы свяжемся с вами для обсуждения покупки!\n\n"
        "📌 <b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/catalog - Каталог песен\n"
        "/wishlist - Ваша корзина"
    )

    keyboard = MainUserKeyboard()(current_user.is_staff)
    await message.answer(help_text, reply_markup=keyboard)


__all__ = ["router"]
