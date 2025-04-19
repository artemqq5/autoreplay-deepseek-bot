from sqlalchemy import (
    BigInteger,
    DateTime,
    String,
    UniqueConstraint,
    func, Text, Integer,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from bot.data.constats import DEFAULT_DEEPSEEK_CONTENT


class Base(DeclarativeBase):
    pass


class AdminsModel(Base):
    __tablename__ = "admins"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    business_id: Mapped[str] = mapped_column(String(255), nullable=True)
    firstname: Mapped[str] = mapped_column(String(255), nullable=True)
    joined: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())  # pylint: disable=not-callable

    def __iter__(self):
        yield from {
            "user_id": self.user_id,
            "business_id": self.business_id,
            "username": self.username,
            "firstname": self.firstname,
            "joined": self.joined.isoformat() if self.joined else None,
        }.items()


class ChatsModel(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[str] = mapped_column(String(255))
    chat_id: Mapped[int] = mapped_column(BigInteger)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default=DEFAULT_DEEPSEEK_CONTENT)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    firstname: Mapped[str] = mapped_column(String(255), nullable=True)
    created: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())  # pylint: disable=not-callable

    __table_args__ = (UniqueConstraint("chat_id", "business_id", name="uq_chat"),)

    def __iter__(self):
        yield from {
            "id": self.id,
            "business_id": self.business_id,
            "prompt": self.prompt,
            "chat_id": self.chat_id,
            "username": self.username,
            "firstname": self.firstname,
            "created": self.created.isoformat() if self.created else None,
        }.items()

