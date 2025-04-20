import asyncio
import logging
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
pending_messages: dict[tuple[str, int], list[list[Message]]] = {}
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

    now = datetime.utcnow()
    last_msg[key] = now

    # ініціалізація черги
    if key not in pending_messages:
        pending_messages[key] = [[]]  # перший пакет

    # додаємо в останній (активний) пакет
    pending_messages[key][-1].append(message)

    task = pending_tasks.get(key)

    if not task or task.done():
        pending_tasks[key] = asyncio.create_task(process_debounced(bot, key))
    else:
        logging.debug(f"📨 Повідомлення записано в буфер до активного завдання — {key}")

    return True


async def process_debounced(bot: Bot, key: tuple[str, int]):
    bc_id, user_id = key

    while pending_messages.get(key):  # поки є черги
        # чекаємо тишу
        while True:
            await asyncio.sleep(DEBOUNCE_SECONDS)
            now = datetime.utcnow()
            last_time = last_msg.get(key)
            if last_time and (now - last_time).total_seconds() >= DEBOUNCE_SECONDS:
                break

        message_batches = pending_messages.get(key)
        if not message_batches:
            return

        messages = message_batches.pop(0)  # обробляємо найстаріший пакет

        last_msg_obj = messages[-1]
        combined_text = "\n".join(
            filter(None, (DeepSeekAPI._norm_text(m.text) for m in messages))
        )
        if not combined_text:
            continue

        logging.info(
            f"\n📥 Новий пакет з {len(messages)} повідомлень від {key}:\n---\n{combined_text}\n---"
        )

        chat = await ChatRepository().chat(user_id, bc_id)

        try:
            await bot.read_business_message(
                business_connection_id=bc_id,
                chat_id=last_msg_obj.chat.id,
                message_id=last_msg_obj.message_id,
            )

            response = await deepseek.make_request(
                chat_id=last_msg_obj.chat.id,
                user_message=combined_text,
                system_prompt=chat['prompt']
            )

            if not response:
                continue

            words = max(1, len(response.split()))
            reading_time = words / WORDS_PER_SEC * random.uniform(*EXTRA_JITTER)
            await asyncio.sleep(reading_time)

            if random.random() < 0.35:
                await bot.send_message(
                    chat_id=last_msg_obj.chat.id,
                    text=response,
                    business_connection_id=bc_id,
                    reply_to_message_id=last_msg_obj.message_id
                )
            else:
                await last_msg_obj.answer(response)

        except Exception as e:
            logging.error(f"[Debounced handler] Помилка для {key}: {e}")
