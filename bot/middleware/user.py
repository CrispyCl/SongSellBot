from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, Update

from service import UserService


class CurrentUserMiddleware(BaseMiddleware):
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ):
        if event.message:
            user = event.message.from_user
        elif event.callback_query:
            user = event.callback_query.from_user

        username = user.username or f"user_{user.id}"

        current_user = await self.user_service.get_or_create(id=str(user.id), username=username)
        await self.user_service.update_username(current_user.id, username)

        data["current_user"] = current_user
        return await handler(event, data)


__all__ = ["CurrentUserMiddleware"]
