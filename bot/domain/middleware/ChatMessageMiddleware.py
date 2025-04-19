import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject

from bot.data.repository.AdminRepository import AdminRepository
from bot.data.repository.ChatRepository import ChatRepository


class ChatMessageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        if not isinstance(event, types.Message):
            return

        business_id = event.business_connection_id
        chat_id = event.chat.id

        chat = await ChatRepository().chat(chat_id, business_id)

        if not chat:
            logging.info(f"Chat ({business_id}) not exists")
            if not await ChatRepository().add(business_id, chat_id, event.chat.username, event.chat.first_name):
                logging.info(f"Can`t add chat with id ({chat_id})")
                return
            logging.info(f"Chat ({chat_id}) added Successfuly!")

        return await handler(event, data)
