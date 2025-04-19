import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject

from bot.data.repository.AdminRepository import AdminRepository
from bot.data.repository.ChatRepository import ChatRepository


class ClientBusinessMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:

        if not isinstance(event, types.Message):
            return

        if event.from_user.id == event.chat.id:
            return await handler(event, data)



