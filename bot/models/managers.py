from contextlib import asynccontextmanager
from logging import getLogger
from typing import Any, AsyncIterator, Dict, List, Sequence, Tuple

from sqlalchemy import MetaData, func, inspect, make_url, or_, select
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import joinedload, lazyload, load_only, noload
from sqlalchemy.orm.strategy_options import _AbstractLoad  # noqa
from sqlalchemy.util import FacadeDict

from models.mixins import CRUDMixin
from models.schemas import Association, Base, Channel, Temp, User


class DatabaseAsyncSessionManager:
    tables: FacadeDict = Base.metadata.tables
    metadata: MetaData = Base.metadata

    logger = getLogger(__name__)

    def __init__(self) -> None:
        self._engine_url: URL | str | None = None
        self._init_db: bool = False
        self._async_engine: AsyncEngine | None = None
        self._async_sessionmaker: async_sessionmaker[AsyncSession] | None = None

    def init(
        self,
        engine_url: URL | str,
        connect_args: Dict | None = None,
        echo_sql: bool = False,
        init_db: bool = False,
    ) -> None:
        self._engine_url = make_url(engine_url)

        if not connect_args:
            connect_args = {}

        if "postgresql" in self._engine_url.drivername:
            connect_args.update(
                {
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0,
                },
            )

        self._init_db = init_db

        self._async_engine: AsyncEngine = create_async_engine(
            self._engine_url,
            echo=echo_sql,
            connect_args=connect_args,
        )
        self._async_sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self._async_engine,
            expire_on_commit=False,
        )

    async def __initialise_db(self) -> None:
        async with self.connect() as conn:
            await conn.run_sync(self.metadata.create_all)

        self.logger.warning("Database is initialized")

    async def close(self) -> None:
        if self._async_engine is None:
            return
        await self._async_engine.dispose()
        self._async_engine = None
        self._async_sessionmaker = None

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._async_sessionmaker is None:
            raise IOError(f"{self} is not initialized")

        async with self._async_sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._async_engine is None:
            raise IOError(f"{self} is not initialized")

        async with self._async_engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    async def __check_missing_tables(
        self,
        missing_tables: List[str],
    ) -> None:
        if missing_tables:
            if self._init_db:
                await self.__initialise_db()
            else:
                exc_text = f"Tables not found: [{', '.join(missing_tables)}]"
                self.logger.critical(exc_text)
                raise ValueError(exc_text)

    def __check_tables(self, database_tables: List[str]) -> List[str]:
        self.logger.debug("Checking tables...")

        missing_tables = []

        for table in self.tables:
            if table not in database_tables:
                missing_tables.append(table)

        if missing_tables:
            self.logger.warning(
                "Tables (%s) not in database tables (%s).",
                ", ".join(missing_tables),
                database_tables,
            )

        return missing_tables

    async def inspect(self) -> None:
        async with self.connect() as async_conn:
            tables = await async_conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names(),
            )
            await self.__check_missing_tables(self.__check_tables(tables))

        self.logger.debug("Database connected")

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        name = self.__class__.__name__
        driver = self._engine_url.drivername
        database = self._engine_url.database
        return f"{name}[{driver}]:{database}"


class UserManager(CRUDMixin):
    table = User

    async def get_with_channel_limit(
        self,
        async_session: AsyncSession,
        user_id: int,
        options: List[_AbstractLoad] | None = None,
        order_by: Any | None = None,
        limit: int = CRUDMixin.default_limit,
    ) -> Tuple[User, bool] | Tuple[None, None]:
        if not options:
            options = []

        options.append(  # No load channels relationship
            lazyload(self.table.channels).lazyload(Association.channel),
        )

        stmt = (
            select(
                self.table,
                func.count(self.table.channels)
                >= self.table.default_subs_count + self.table.add_subs_count,
            )
            .join_from(self.table, Association, isouter=True)
            .join_from(Association, Channel, isouter=True)
            .where(User.telegram_id == user_id)
            .group_by(self.table.id)
            .options(*options)
            .order_by(self.ordering(order_by))
            .limit(limit)
        )

        res = await async_session.execute(stmt)
        res = res.unique().all()

        return res[0] if res else (None, None)


class ChannelManager(CRUDMixin):
    table = Channel

    async def get_by_url(
        self,
        async_session: AsyncSession,
        url: str,
    ) -> Channel | None:
        """
        Loaded fields:
        id, name, url
        """
        options = [
            load_only(Channel.id, Channel.name, Channel.url),
            noload(Channel.users),
        ]

        result = await self.get(
            async_session,
            where=[or_(Channel.url == url, Channel.canonical_url == url)],
            options=options,
            limit=1,
        )

        return result[0] if result else None

    async def get_user_channels(
        self,
        async_session: AsyncSession,
        user_id: int,
        order_by: Any | None = None,
        limit: int = CRUDMixin.default_limit,
    ) -> Sequence[Channel]:
        """
        Loaded fields:
        id, name, url
        """
        options = [  # No load user relationship
            load_only(Channel.id, Channel.name, Channel.url),
            lazyload(Channel.users).lazyload(Association.user),
        ]

        stmt = (
            select(self.table)
            .where(User.telegram_id == user_id)
            .join_from(self.table, Association)
            .join_from(Association, User)
            .options(*options)
            .order_by(self.ordering(order_by))
            .limit(limit)
        )

        res = await async_session.scalars(stmt)
        return res.unique().all()

    async def get_channels_with_users(  # Todo normalise sql request
        self,
        async_session: AsyncSession,
        order_by: Any | None = None,
        limit: int = CRUDMixin.default_limit,
    ) -> Sequence[Channel]:
        options = [
            joinedload(Channel.users)
            .joinedload(Association.user)
            .load_only(User.telegram_id, User.blocked),
        ]

        stmt = (
            select(self.table)
            .where(User.blocked.is_(False))
            .join_from(self.table, Association)
            .join_from(Association, User)
            .options(*options)
            .order_by(self.ordering(order_by))
            .limit(limit)
        )

        res = await async_session.scalars(stmt)
        return res.unique().all()

    async def add_with_association(
        self,
        async_session: AsyncSession,
        user: User,
        channel: Channel,
    ) -> Channel:
        association = Association()
        association.user = user

        channel.users.append(association)
        return await self.add(async_session, channel)


class AssociationManager(CRUDMixin):
    table = Association

    async def exists(  # noqa
        self,
        async_session: AsyncSession,
        user: User,
        channel: Channel,
    ) -> bool:
        where = [Association.channel_id == channel.id, Association.user_id == user.id]
        options = [
            load_only(Association.id),
            noload(Association.user),
            noload(Association.channel),
        ]
        return await super().exists(async_session, where, options)

    async def delete(  # noqa
        self,
        async_session: AsyncSession,
        user: User,
        channel: Channel,
    ) -> bool:
        where = [Association.channel_id == channel.id, Association.user_id == user.id]
        return await super().delete(async_session, where)


class TempManager(CRUDMixin):
    table = Temp

    async def get_all(
        self,
        async_session: AsyncSession,
        order_by: Any | None = None,
        limit: int = CRUDMixin.default_limit,
    ) -> Sequence[Temp]:
        return await self.get(async_session, order_by=order_by, limit=limit)


db_session_manager = DatabaseAsyncSessionManager()


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    async with db_session_manager.session() as session:
        yield session
