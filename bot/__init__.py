from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import DB_LINK_CONNECTION

engine = create_async_engine(DB_LINK_CONNECTION)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
