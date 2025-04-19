import math

from aiogram.filters.callback_data import CallbackData
from aiogram_i18n import L
from aiogram_i18n.types import InlineKeyboardButton, InlineKeyboardMarkup


class ChatDetail(CallbackData, prefix="ChatDetail"):
    id: int


class ChatsNavigation(CallbackData, prefix="ChatsNavigation"):
    page: int


def kb_chats_nav(chats, current_page: int = 1):
    inline_kb = []

    # if items less then pages exist before -> Leave to 1 page
    if len(chats) < (current_page * 10) - 9:
        current_page = 1

    total_pages = math.ceil(len(chats) / 10)
    start_index = (current_page - 1) * 10
    end_index = min(start_index + 10, len(chats))

    # load from db
    for i in range(start_index, end_index):
        inline_kb.append(
            [
                InlineKeyboardButton(
                    text=f"#{chats[i]['id']} {chats[i]['firstname']}",
                    callback_data=ChatDetail(id=chats[i]["id"]).pack(),
                )
            ]
        )

    if len(chats) > 10:
        nav = []

        if current_page > 1:
            nav.append(InlineKeyboardButton(text="◀️", callback_data=ChatsNavigation(page=current_page - 1).pack()))

        nav.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="None"))

        if current_page < total_pages:
            nav.append(InlineKeyboardButton(text="▶️", callback_data=ChatsNavigation(page=current_page + 1).pack()))

        inline_kb.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


class ChatsBack(CallbackData, prefix="ChatsBack"):
    pass


class ChatBack(CallbackData, prefix="ChatBack"):
    pass


class ChangePromptChat(CallbackData, prefix="ChangePromptChat"):
    pass


kb_chat_detail = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=L.CHAT.CHANGE_PROMPT(), callback_data=ChangePromptChat().pack())],
    [InlineKeyboardButton(text=L.BACK(), callback_data=ChatsBack().pack())]
])

kb_chat_back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=L.BACK(), callback_data=ChatBack().pack())]
])
