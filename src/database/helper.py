import threading
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from logging import getLogger

from sqlalchemy import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = getLogger(__name__)


class AsyncDatabase:
    def __init__(self) -> None:
        self._engine_url: URL | str | None = None
        self._async_engine: AsyncEngine | None = None
        self._async_sessionmaker: async_sessionmaker[AsyncSession] | None = None

    @property
    def status(self) -> str:
        return "Connected" if self._async_engine else "Disconnected"

    async def init(
        self,
        engine_url: URL | str,
        connect_args: dict | None = None,
        echo_sql: bool = False,
        echo_pool: bool = False,
        max_overflow: int = 10,
        pool_size: int = 5,
    ) -> None:
        self._engine_url = make_url(engine_url)

        engine_args = {
            "echo": echo_sql,
            "echo_pool": echo_pool,
            "max_overflow": max_overflow,
            "pool_size": pool_size,
        }

        if not connect_args:
            connect_args = {}

        if "postgresql" in self._engine_url.drivername:
            connect_args.update(
                {
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0,
                },
            )

        elif "sqlite" in self._engine_url.drivername:
            engine_args.pop("max_overflow")
            engine_args.pop("pool_size")

        self._async_engine: AsyncEngine = create_async_engine(
            self._engine_url, connect_args=connect_args, **engine_args
        )
        self._async_sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self._async_engine,
            expire_on_commit=False,
        )

        await self.__check_connect()

    async def __check_connect(self) -> None:
        try:
            async with self.connect():
                logger.info(f"%s %s", self, self.status)

        except Exception as ex:
            logger.critical(f"%s Connection failed. %s", self, ex)
            raise ex

    async def close(self) -> None:
        if self._async_engine is None:
            return

        await self._async_engine.dispose()

        self._async_engine = None
        self._async_sessionmaker = None

        logger.info(f"%s %s", self, self.status)

    @asynccontextmanager
    async def session(self) -> AbstractAsyncContextManager[AsyncSession]:
        if self._async_sessionmaker is None:
            raise IOError(f"{self.__repr__()} is not initialized")

        async with self._async_sessionmaker() as session:  # type: AsyncSession
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def connect(self) -> AbstractAsyncContextManager[AsyncConnection]:
        if self._async_engine is None:
            raise IOError(f"{self} is not initialized")

        async with self._async_engine.begin() as connection:  # type: AsyncConnection
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    def __repr__(self) -> str:
        thread = threading.current_thread()
        thread_repr = f"{thread.name}, {thread.native_id}"

        if self._engine_url:
            args = {
                "driver": self._engine_url.drivername,
                "database": self._engine_url.database,
                "user": self._engine_url.username,
                "host": self._engine_url.host,
                "port": self._engine_url.port,
            }

        else:
            args = {}

        res = ", ".join([f"{k}={v}" for k, v in args.items() if v])
        return (
            f"{self.__class__.__name__}[{thread_repr}]({res if res else 'not connected'})"
        )
