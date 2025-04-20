import logging
from collections import defaultdict

from openai import AsyncOpenAI

from bot.config import DEEPDEEK_KEY
from bot.data.constats import DEFAULT_DEEPSEEK_CONTENT


class DeepSeekAPI:

    def __init__(self):
        self.__client = AsyncOpenAI(api_key=DEEPDEEK_KEY, base_url="https://api.deepseek.com")
        self._dialogs = defaultdict(list)

    @staticmethod
    def _norm_text(raw: str | None) -> str | None:
        """Оставляем только непустые текстовые сообщения."""
        if raw is None:
            return None
        raw = raw.strip()
        return raw if raw else None

    async def make_request(self, chat_id: int, user_message: str, system_prompt: str = DEFAULT_DEEPSEEK_CONTENT):
        try:

            history = self._dialogs[chat_id]

            if not history:
                history.append({"role": "system", "content": system_prompt})
            else:
                history[0]["content"] = system_prompt

            history.append({"role": "user", "content": user_message})

            response = await self.__client.chat.completions.create(
                model="deepseek-chat",
                messages=history,
                temperature=0.7,
                stream=False
            )

            assistant_reply = response.choices[0].message.content

            # 3. зберігаємо відповідь асистента в історії
            history.append({"role": "assistant", "content": assistant_reply})

            # 4. (опційно) обрізаємо історію до N останніх повідомлень
            MAX_TURNS = 20
            if len(history) > MAX_TURNS * 2 + 1:  # *2 бо user+assistant
                # залишаємо system + останні MAX_TURNS пар
                self._dialogs[chat_id] = [history[0]] + history[-MAX_TURNS * 2:]

            # лог
            logging.info(
                "Chat %s | Q: %s | A: %s", chat_id, user_message, assistant_reply
            )
            return assistant_reply
        except Exception as e:
            logging.error(e)
            return None
