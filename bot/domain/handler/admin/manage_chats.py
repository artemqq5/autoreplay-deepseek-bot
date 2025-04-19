from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram_i18n import I18nContext

from bot.data.repository.AdminRepository import AdminRepository
from bot.data.repository.ChatRepository import ChatRepository
from bot.domain.handler.admin import change_prompt
from bot.keyboard.admin.kb_chats_nav import kb_chats_nav, ChatDetail, ChatsNavigation, kb_chat_detail, ChatBack, \
    ChatsBack

router = Router()

router.include_router(change_prompt.router)


@router.message(Command("chats"))
async def chats_(message: Message, state: FSMContext, i18n: I18nContext):
    admin = await AdminRepository().admin(message.from_user.id)
    chats = await ChatRepository().chats(admin['business_id'])
    await state.update_data(business_id=admin['business_id'])
    await message.answer(i18n.CHATS(), reply_markup=kb_chats_nav(chats, 1))


@router.callback_query(ChatsNavigation.filter())
async def chats_nav_call(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()

    await state.update_data(last_page_chats=page)
    chats = await ChatRepository().chats(data['business_id'])

    await callback.message.edit_text(text=i18n.CHATS(), reply_markup=kb_chats_nav(chats, current_page=page))


@router.callback_query(ChatDetail.filter())
async def chat_detail_call(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    _id = int(callback.data.split(":")[1])
    chat = await ChatRepository().chat_by_id(_id)

    if not chat:
        await callback.answer("not exist")
        return

    await state.update_data(chat=chat)

    await callback.message.edit_text(
        i18n.CHAT.DETAIL(
            id=str(chat["id"]),
            chat_id=str(chat["chat_id"]),
            username=f"@{chat['username']}" if chat.get("username") else "-",
            firstname=chat['firstname'],
            prompt=chat["prompt"],
        ),
        reply_markup=kb_chat_detail,
    )


@router.callback_query(ChatsBack.filter())
async def chats_back_call(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    data = await state.get_data()
    chats = await ChatRepository().chats(data['business_id'])
    await callback.message.edit_text(i18n.CHATS(), reply_markup=kb_chats_nav(chats, data.get("last_page_chats", 1)))


@router.callback_query(ChatBack.filter())
async def chat_back_call(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    data = await state.get_data()
    chat = await ChatRepository().chat_by_id(data['chat']['id'])

    if not chat:
        await callback.answer("not exist")
        return

    await state.update_data(chat=chat)

    await callback.message.answer(
        i18n.CHAT.DETAIL(
            id=str(chat["id"]),
            chat_id=str(chat["chat_id"]),
            username=f"@{chat['username']}" if chat.get("username") else "-",
            firstname=chat['firstname'],
            prompt=chat["prompt"],
        ),
        reply_markup=kb_chat_detail,
    )
