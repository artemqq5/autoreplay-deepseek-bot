import asyncio
import logging
import random
from datetime import datetime, timedelta

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


@router.business_message()
async def handle_business_message(message: Message, bot: Bot):
    user_text = DeepSeekAPI._norm_text(message.text)
    if not user_text:
        return True

    bc_id = message.business_connection_id
    user_id = message.from_user.id
    key = (bc_id, user_id)

    chat = await ChatRepository().chat(user_id, bc_id)

    now = datetime.utcnow()
    last_seen = last_msg.get(key)
    last_msg[key] = now  # обновим тайм‑стамп сразу

    # ── 1.  Задержка «менеджер увидел»
    delay_needed = True
    if last_seen and (now - last_seen) < timedelta(seconds=60):
        delay_needed = False  # было сообщение <15сек назад

    if delay_needed:
        await asyncio.sleep(random.randint(MIN_DELAY, MAX_DELAY))

    # Помечаем прочитанным
    await bot.read_business_message(
        business_connection_id=bc_id,
        chat_id=message.chat.id,
        message_id=message.message_id,
    )

    # ── 2.  Генерируем ответ от DeepSeek
    response = await deepseek.make_request(
        chat_id=message.chat.id,
        user_message=user_text,
        system_prompt=chat['prompt']
    )
    if not response:
        logging.info("DeepSeek вернул пустой ответ")
        return True

    # ── 3.  «Чтение» перед отправкой
    words = max(1, len(response.split()))
    reading_time = words / WORDS_PER_SEC * random.uniform(*EXTRA_JITTER)
    await asyncio.sleep(reading_time)

    # ── 4. 65% шанс ответить reply
    if random.random() < 0.35:
        await bot.send_message(
            chat_id=message.chat.id,
            text=response,
            business_connection_id=message.business_connection_id,  # ← головне
            reply_to_message_id=message.message_id  # робить саме «відповідь»
        )
    else:
        await message.answer(response)

    return True
