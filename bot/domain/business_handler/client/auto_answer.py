import asyncio
import random
from datetime import datetime

from aiogram import Router, Bot
from aiogram.types import Message

from bot.data.api.DeepSeekAPI import DeepSeekAPI
from bot.data.repository.ChatRepository import ChatRepository
from bot.domain.middleware.ChatMessageMiddleware import ChatMessageMiddleware
from bot.domain.middleware.ClientBusinessMiddleware import ClientBusinessMiddleware

router = Router()
deepseek = DeepSeekAPI()

router.business_message.middleware(ChatMessageMiddleware())
router.business_message.middleware(ClientBusinessMiddleware())

#  базовая «реакция» — задержка, если предыдущее сообщение было давно
MIN_DELAY, MAX_DELAY = 5, 30  # сек
WORDS_PER_SEC = 200 / 60  # ≈3слова/сек
EXTRA_JITTER = (0.8, 1.2)

#  запоминаем время последнего сообщения клиента в этом bc‑чате
last_msg: dict[tuple[str, int], datetime] = {}  # (bc_id, user_id) -> ts

# зберігаємо: (bc_id, user_id) -> [повідомлення]
pending_messages: dict[tuple[str, int], list[Message]] = {}
pending_tasks: dict[tuple[str, int], asyncio.Task] = {}
DEBOUNCE_SECONDS = 5


@router.business_message()
async def handle_business_message(message: Message, bot: Bot):
    user_text = DeepSeekAPI._norm_text(message.text)
    if not user_text:
        return True

    bc_id = message.business_connection_id
    user_id = message.from_user.id
    key = (bc_id, user_id)

    # запам'ятовуємо останній час
    now = datetime.utcnow()
    last_msg[key] = now

    # кладемо повідомлення в буфер
    pending_messages.setdefault(key, []).append(message)

    # якщо вже є задача очікування — скасовуємо і створюємо нову
    task = pending_tasks.get(key)
    if task and not task.done():
        task.cancel()

    pending_tasks[key] = asyncio.create_task(
        process_debounced(bot, key)
    )

    return True


async def process_debounced(bot: Bot, key: tuple[str, int]):
    await asyncio.sleep(DEBOUNCE_SECONDS)

    bc_id, user_id = key
    messages = pending_messages.pop(key, [])
    if not messages:
        return

    last_msg_obj = messages[-1]
    combined_text = "\n".join(
        filter(None, (DeepSeekAPI._norm_text(m.text) for m in messages))
    )

    if not combined_text:
        return

    # дістаємо промпт
    chat = await ChatRepository().chat(user_id, bc_id)

    # імітація «бачу повідомлення»
    await bot.read_business_message(
        business_connection_id=bc_id,
        chat_id=last_msg_obj.chat.id,
        message_id=last_msg_obj.message_id,
    )

    # запит до DeepSeek
    response = await deepseek.make_request(
        chat_id=last_msg_obj.chat.id,
        user_message=combined_text,
        system_prompt=chat['prompt']
    )

    if not response:
        return

    # читаємо як «менеджер»
    words = max(1, len(response.split()))
    reading_time = words / WORDS_PER_SEC * random.uniform(*EXTRA_JITTER)
    await asyncio.sleep(reading_time)

    # випадкова відповідь як reply або просто message
    if random.random() < 0.35:
        await bot.send_message(
            chat_id=last_msg_obj.chat.id,
            text=response,
            business_connection_id=bc_id,
            reply_to_message_id=last_msg_obj.message_id
        )
    else:
        await last_msg_obj.answer(response)
