from sqlalchemy import insert, select, update

from bot.data.BaseRepository import BaseRepository
from bot.data.sqlmodels import ChatsModel


class ChatRepository(BaseRepository[ChatsModel]):

    async def add(self, business_id, chat_id, username, firstname):
        query = insert(ChatsModel).values(business_id=business_id, chat_id=chat_id, username=username,
                                          firstname=firstname)
        return await self._insert(query)

    async def chat(self, chat_id, business_id):
        query = select(ChatsModel).where(ChatsModel.business_id == business_id, ChatsModel.chat_id == chat_id).limit(1)
        return await self._select(query)

    async def chat_by_id(self, _id):
        query = select(ChatsModel).where(ChatsModel.id == _id).limit(1)
        return await self._select(query)

    async def chats(self, business_id):
        query = select(ChatsModel).where(ChatsModel.business_id == business_id)
        return await self._select_all(query)

    async def update_chat_prompt(self, _id, prompt):
        query = update(ChatsModel).values(prompt=prompt).where(ChatsModel.id == _id)
        return await self._update(query)
