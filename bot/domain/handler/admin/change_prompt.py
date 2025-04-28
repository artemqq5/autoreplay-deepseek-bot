from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext

from bot.data.repository.ChatRepository import ChatRepository
from bot.domain.state.ChangePromptState import ChangePromptState
from bot.keyboard.admin.kb_chats_nav import kb_chat_back, ChangePromptChat

router = Router()


@router.callback_query(ChangePromptChat.filter())
async def chat_prompt_change(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    await state.set_state(ChangePromptState.Prompt)
    await callback.message.edit_text(i18n.CHAT.CHANGE_PROMPT.SET_NEW(), reply_markup=kb_chat_back)


@router.message(ChangePromptState.Prompt)
async def set_new_prompt(message: Message, state: FSMContext, i18n: I18nContext):
    await state.set_state(None)

    prompt = message.text
    data = await state.get_data()

    if not await ChatRepository().update_chat_prompt(data['chat']['id'], prompt):
        await message.answer(i18n.CHAT.CHANGE_PROMPT.FAIL(), reply_markup=kb_chat_back)
        return

    await message.answer(i18n.CHAT.CHANGE_PROMPT.SUCCESS(), reply_markup=kb_chat_back)
