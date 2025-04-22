import asyncio
import logging
import os
import random
from datetime import datetime
from tempfile import NamedTemporaryFile

import whisper
from aiogram import Router, Bot, F
from aiogram.types import Message
from anyio import sleep
from pydub import AudioSegment

from bot.data.api.DeepSeekAPI import DeepSeekAPI
from bot.data.repository.ChatRepository import ChatRepository
from bot.domain.middleware.ChatMessageMiddleware import ChatMessageMiddleware
from bot.domain.middleware.ClientBusinessMiddleware import ClientBusinessMiddleware

router = Router()
deepseek = DeepSeekAPI()

router.business_message.middleware(ChatMessageMiddleware())
router.business_message.middleware(ClientBusinessMiddleware())

model = whisper.load_model("base")

#  базовая «реакция» — задержка, если предыдущее сообщение было давно
MIN_DELAY, MAX_DELAY = 5, 30  # сек
WORDS_PER_SEC = 200 / 100  # ≈3слова/сек
EXTRA_JITTER = (0.8, 1.2)

#  запоминаем время последнего сообщения клиента в этом bc‑чате
last_msg: dict[tuple[str, int], datetime] = {}  # (bc_id, user_id) -> ts

# зберігаємо: (bc_id, user_id) -> [повідомлення]
pending_messages: dict[tuple[str, int], list[list[Message]]] = {}
pending_tasks: dict[tuple[str, int], asyncio.Task] = {}
DEBOUNCE_SECONDS = 5


@router.business_message(F.text)
async def handle_business_message(message: Message, bot: Bot):
    user_text = DeepSeekAPI._norm_text(message.text)
    if not user_text:
        return True

    bc_id = message.business_connection_id
    user_id = message.from_user.id
    key = (bc_id, user_id)

    now = datetime.utcnow()
    last_msg[key] = now

    # Ініціалізація черги пакетів
    if key not in pending_messages or not pending_messages[key]:
        pending_messages[key] = [[]]
    pending_messages[key][-1].append(message)

    task = pending_tasks.get(key)

    # 🧠 Якщо вже є активна задача — читаємо повідомлення одразу (бот "в діалозі")
    if task and not task.done():
        await bot.read_business_message(
            business_connection_id=bc_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
        # logging.debug(f"👁 Прочитав одразу (в діалозі): {message.text}")
    else:
        # 🕐 Якщо немає активної задачі — запускаємо debounce
        logging.debug(f"▶️ Запускаємо нову задачу на обробку")
        pending_tasks[key] = asyncio.create_task(process_debounced(bot, key))

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

        # logging.info(
        #     f"\n📥 Новий пакет з {len(messages)} повідомлень від {key}:\n---\n{combined_text}\n---"
        # )

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

            if len(messages) == 1:
                await messages[0].answer(response)
            else:
                await bot.send_message(
                    chat_id=last_msg_obj.chat.id,
                    text=response,
                    business_connection_id=bc_id,
                    reply_to_message_id=last_msg_obj.message_id
                )

        except Exception as e:
            logging.error(f"[Debounced handler] Помилка для {key}: {e}")


@router.business_message(F.voice)
async def handle_business_voice(message: Message, bot: Bot):
    bc_id = message.business_connection_id
    user_id = message.from_user.id
    key = (bc_id, user_id)

    file_id = message.voice.file_id
    file = await bot.get_file(file_id)

    with NamedTemporaryFile(delete=False, suffix=".ogg") as ogg_temp:
        await bot.download_file(file.file_path, destination=ogg_temp.name)
        ogg_path = ogg_temp.name

    wav_path = ogg_path.replace(".ogg", ".wav")

    try:
        # Конвертуємо ogg → wav
        audio = AudioSegment.from_file(ogg_path)
        audio.export(wav_path, format="wav")

        # Транскрипція
        result = model.transcribe(wav_path)
        text = result.get("text", "").strip()
        if not text:
            return

        await bot.read_business_message(
            business_connection_id=bc_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
        )

        # logging.info(f"🎤 Розпізнано voice: {text}")
        chat = await ChatRepository().chat(user_id, bc_id)
        response = await deepseek.make_request(
            chat_id=message.chat.id,
            user_message=text,
            system_prompt=chat['prompt']
        )

        if not response:
            return

        await bot.send_message(
            chat_id=message.chat.id,
            text=response,
            business_connection_id=bc_id,
            reply_to_message_id=message.message_id
        )

    except Exception as e:
        logging.error(f"[Voice Handler] {e}")

    finally:
        for path in [ogg_path, wav_path]:
            try:
                os.remove(path)
            except Exception as e:
                logging.warning(f"Не вдалося видалити файл {path}: {e}")
