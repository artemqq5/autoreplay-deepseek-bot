import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject

from bot.data.repository.AdminRepository import AdminRepository


class AdminBusinessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        if not isinstance(event, (types.Message, types.BusinessConnection)):
            return

        user_id = event.user.id
        admin = await AdminRepository().admin(user_id)

        if not admin:
            logging.info(f"User({user_id}) isn`t admin and can`t create chats with bot")
            return

        if admin.get('business_id', None):
            return

        return await handler(event, data)

