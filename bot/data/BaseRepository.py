import logging
from typing import Generic, TypeVar

from sqlalchemy import text

from bot import async_session, engine
from bot.data.sqlmodels import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self):
        self.engine = engine
        self.async_session = async_session

    async def _select(self, query):
        try:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(query)
                    data = result.scalar_one_or_none()
                    return dict(data) if data else None
        except Exception as e:
            logging.error(e)
            return None

    async def _select_all(self, query):
        try:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(query)
                    list_data = result.scalars().all() or []
                    return [dict(data) for data in list_data]
        except Exception as e:
            logging.error(e)
            return None

    async def _insert(self, query):
        try:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(query)
                    return result.rowcount
        except Exception as e:
            logging.error(e)
            return None

    async def _insert_with_last_id(self, query):
        try:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(query)
                    if result.rowcount >= 1:
                        result = await session.execute(text("SELECT LAST_INSERT_ID() as lid"))
                        inserted_id = result.scalar()
                        return inserted_id
                    return None
        except Exception as e:
            logging.error(e)
            return None

    async def _update(self, query):
        try:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(query)
                    return result.rowcount
        except Exception as e:
            logging.error(e)
            return None

    async def _delete(self, query):
        try:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(query)
                    return result.rowcount
        except Exception as e:
            logging.error(e)
            return None
