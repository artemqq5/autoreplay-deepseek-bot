import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore

from bot.config import BOT_TOKEN
from bot.domain.business_handler.admin import create_chat_with_bot
from bot.domain.business_handler.client import auto_answer
from bot.domain.handler.admin import manage_chats
from bot.domain.middleware.LocalManager import LocaleManager

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_routers(
    create_chat_with_bot.router,
    auto_answer.router,
    manage_chats.router
)


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=BOT_TOKEN, default=default_properties)

    i18n_middleware = I18nMiddleware(
        core=FluentRuntimeCore(path="locales"),
        default_locale="uk",
        manager=LocaleManager(),
    )

    i18n_middleware.setup(dp)

    # start bot
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
