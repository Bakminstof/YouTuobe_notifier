from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Sequence, Tuple

from sqlalchemy import (
    BOOLEAN,
    SMALLINT,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    delete,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import BIGINT
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Mapped,
    lazyload,
    load_only,
    mapped_column,
    noload,
    relationship,
)

from db.declarative_base import Base
from db.mixins import CRUDMixin


class Association(Base, CRUDMixin):
    __tablename__ = "association"
    __table_args__ = (UniqueConstraint("user_id", "channel_id", name="_user_channel_uc"),)

    id: Mapped[int] = mapped_column(
        "id", BIGINT, autoincrement=True, nullable=False, unique=True, primary_key=True
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="channels", lazy="joined")
    channel: Mapped["Channel"] = relationship(back_populates="users", lazy="joined")

    # extra_data: Mapped[Optional[str]]

    @classmethod
    async def add_association(
        cls,
        user: User,
        channel: Channel,
        async_session: async_sessionmaker[AsyncSession],
    ) -> None:
        """
        Добавить связь канала с пользователем.
        """
        async with async_session() as session:
            async with session.begin():
                a = Association(user_id=user.id, channel_id=channel.id)
                session.add(a)
                await session.commit()

    @classmethod
    async def check(
        cls,
        user: User,
        channel: Channel,
        async_session: async_sessionmaker[AsyncSession],
    ) -> Association:
        """
        Проверить наличие связи пользователя с каналом.
        """
        async with (async_session() as session):
            async with session.begin():
                stmt = (
                    select(cls)
                    .where(cls.channel_id == channel.id, cls.user_id == user.id)
                    .options(load_only(cls.id), noload(cls.user), noload(cls.channel))
                )

                return await session.scalar(stmt)

    @classmethod
    async def delete(
        cls,
        user: User,
        channel: Channel,
        async_session: async_sessionmaker[AsyncSession],
    ) -> bool:
        """
        Удалить связь пользователя с каналом.
        """
        async with async_session() as session:
            async with session.begin():
                stmt = (
                    delete(cls)
                    .where(cls.channel_id == channel.id)
                    .where(cls.user_id == user.id)
                )

                result = await session.execute(stmt)
                await session.commit()
                return bool(result.__getattribute__("rowcount"))


class User(Base, CRUDMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        "id", BIGINT, autoincrement=True, nullable=False, unique=True, primary_key=True
    )
    telegram_id: Mapped[int] = mapped_column(
        "telegram_id", BIGINT, nullable=False, unique=True
    )
    first_name: Mapped[str] = mapped_column("first_name", String(200), nullable=False)
    last_name: Mapped[str] = mapped_column("last_name", String(200), nullable=True)
    add_subs_count: Mapped[int] = mapped_column(
        "add_subs_count", SMALLINT, nullable=False, default=0
    )
    auth_timestamp: Mapped[datetime] = mapped_column(
        "auth_timestamp", DateTime(), nullable=False, default=datetime.now()
    )
    blocked: Mapped[bool] = mapped_column(
        "blocked", BOOLEAN, default=False, nullable=False
    )
    channels: Mapped[List[Association]] = relationship(
        back_populates="user", lazy="joined"
    )

    @classmethod
    async def get_all(
        cls,
        async_session: async_sessionmaker[AsyncSession],
        load_channels: bool = False,
        options_set: List[
            Dict[Callable, Sequence[InstrumentedAttribute]] | Sequence[Any] | Any
        ] = None,
        ordering: InstrumentedAttribute | None = None,
        limit: int | None = None,
    ) -> Sequence[User]:
        """
        Получить всех пользователя с указанными параметрами.
        """
        async with async_session() as session:
            async with session.begin():
                stmt = select(cls)

                if not load_channels:
                    if not options_set:
                        options_set = []
                    options_set.append({noload: cls.channels})

                stmt = cls.build_stmt(stmt, options_set, ordering, limit)

                res = await session.scalars(stmt)
                return res.unique().all()

    @classmethod
    async def get(
        cls,
        where,
        async_session: async_sessionmaker[AsyncSession],
        load_channels: bool = False,
        options_set: List[
            Dict[Callable, Sequence[InstrumentedAttribute]] | Sequence[Any] | Any
        ] = None,
    ) -> User:
        """
        Получить пользователя по заданному условию с указанными параметрами.
        """
        async with async_session() as session:
            async with session.begin():
                stmt = select(cls).where(where)

                if not load_channels:
                    if not options_set:
                        options_set = []
                    options_set.append({noload: cls.channels})

                stmt = cls.build_stmt(stmt, options_set, False)

                return await session.scalar(stmt)

    @classmethod
    async def get_with_channels_limit(
        cls,
        where,
        async_session: async_sessionmaker[AsyncSession],
        options_set: List[
            Dict[Callable, Sequence[InstrumentedAttribute]] | Sequence[Any] | Any
        ] = None,
    ) -> Tuple[User, bool] | Tuple[None, None]:
        async with async_session() as session:
            async with session.begin():
                stmt = (
                    select(cls, func.count(cls.channels) >= 10 + cls.add_subs_count)
                    .where(where)
                    .group_by(cls.id)
                )
                stmt = stmt.join_from(cls, Association).join_from(Association, Channel)

                if not options_set:
                    options_set = []

                options_set.append(lazyload(cls.channels).lazyload(Association.channel))

                stmt = cls.build_stmt(stmt, options_set, False)
                res = await session.execute(stmt)
                res = res.unique().all()

                return res[0] if res else (None, None)


class Channel(Base, CRUDMixin):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(
        "id", BIGINT, autoincrement=True, nullable=False, unique=True, primary_key=True
    )
    name: Mapped[str] = mapped_column("name", String(200), nullable=False)
    url: Mapped[str] = mapped_column("url", String(200), nullable=False, unique=True)
    last_video: Mapped[str] = mapped_column("last_video", String(200), nullable=True)
    last_stream: Mapped[str] = mapped_column("last_stream", String(200), nullable=True)
    users: Mapped[List[Association]] = relationship(
        back_populates="channel", lazy="joined"
    )

    @classmethod
    async def get_user_channels(
        cls,
        where: Any,
        async_session: async_sessionmaker[AsyncSession],
        options_set: List[
            Dict[Callable, Sequence[InstrumentedAttribute]] | Sequence[Any] | Any
        ] = None,
        ordering: InstrumentedAttribute | None = None,
        limit: int | None = None,
    ):
        """
        Получить список каналов по заданному условию с указанными параметрами.
        """
        async with async_session() as session:
            async with session.begin():
                stmt = (
                    select(cls)
                    .where(where)
                    .join_from(cls, Association)
                    .join_from(Association, User)
                )

                stmt = cls.build_stmt(stmt, options_set, ordering, limit)

                res = await session.scalars(stmt)
                return res.unique().all()

    @classmethod
    async def get(
        cls,
        where,
        async_session: async_sessionmaker[AsyncSession],
        load_users: bool = False,
        options_set: List[
            Dict[Callable, Sequence[InstrumentedAttribute]] | Sequence[Any] | Any
        ] = None,
        ordering: InstrumentedAttribute | None = None,
    ) -> Channel:
        """
        Получить канал по заданным условиям.
        """
        async with async_session() as session:
            async with session.begin():
                stmt = select(cls).where(where)

                if not load_users:
                    if not options_set:
                        options_set = []
                    options_set.append({noload: cls.users})

                stmt = cls.build_stmt(stmt, options_set, ordering)

                return await session.scalar(stmt)

    @classmethod
    async def get_channels_with_users(
        cls,
        async_session: async_sessionmaker[AsyncSession],
        options_set: List[
            Dict[Callable, Sequence[InstrumentedAttribute]] | Sequence[Any] | Any
        ] = None,
        ordering: InstrumentedAttribute | None = None,
    ) -> Sequence[Channel]:
        """
        Получить каналы с хотя бы одним пользователем.
        """
        async with async_session() as session:
            async with session.begin():
                stmt = select(cls).where(Association.channel_id == cls.id)

                stmt = cls.build_stmt(stmt, options_set, ordering)

                res = await session.scalars(stmt)
                return res.unique().all()

    @classmethod
    async def add_with_association(
        cls,
        channel: Channel,
        user: User,
        async_session: async_sessionmaker[AsyncSession],
    ) -> None:
        """
        Добавить канал и установить ассоциацию с указанным пользователем.
        """
        async with async_session() as session:
            async with session.begin():
                a = Association()
                a.user = user

                channel.users.append(a)

                session.add(channel)

                await session.commit()


class Temp(Base, CRUDMixin):
    __tablename__ = "temp"

    id: Mapped[int] = mapped_column(
        "id", BIGINT, autoincrement=True, nullable=False, unique=True, primary_key=True
    )
    telegram_id: Mapped[int] = mapped_column("telegram_id", BIGINT, nullable=False)
    text: Mapped[str] = mapped_column("text", String(4096), nullable=True)

    @classmethod
    async def get_all(
        cls,
        async_session: async_sessionmaker[AsyncSession],
        options_set: List[
            Dict[Callable, Sequence[InstrumentedAttribute]] | Sequence[Any] | Any
        ] = None,
        ordering: InstrumentedAttribute | None = None,
        limit: int | None = None,
    ) -> Sequence[Temp]:
        """
        Получить всех пользователя с указанными параметрами.
        """
        async with async_session() as session:
            async with session.begin():
                stmt = select(cls)

                stmt = cls.build_stmt(stmt, options_set, ordering, limit)

                res = await session.scalars(stmt)
                return res.unique().all()


TABLES = [Association, User, Channel, Temp]
