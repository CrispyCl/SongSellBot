from aiogram import Bot
from aiogram.types import BotCommand


async def setup_menu(bot: Bot):
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Перезапустить бота"),
            BotCommand(command="help", description="Информация о боте"),
            BotCommand(command="catalog", description="Каталог песен"),
            BotCommand(command="wishlist", description="Список желаемого"),
        ],
    )


__all__ = ["setup_menu"]
