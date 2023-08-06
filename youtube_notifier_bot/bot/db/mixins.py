from typing import Any, Callable, Dict, List, Sequence, Tuple

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import InstrumentedAttribute


class CRUDMixin:
    def to_dict(self) -> Dict:
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}

    @classmethod
    def build_options(
        cls,
        options_set: List[
            Dict[Callable, Sequence[InstrumentedAttribute]] | Sequence[Any] | Any
        ],
    ) -> List:
        options = []

        for opts in options_set:
            if isinstance(opts, Dict):
                for option, attributes in opts.items():
                    if isinstance(attributes, (Sequence, List, Tuple)):
                        options.append(option(*attributes))
                    else:
                        options.append(option(attributes))
            else:
                options.append(opts)

        return options

    @classmethod
    def build_stmt(
        cls,
        stmt: Any,
        options_set: List[Sequence] = None,
        ordering: InstrumentedAttribute | None = None,
        limit: int | None = None,
    ) -> Any:
        if options_set:
            options = cls.build_options(options_set)
            stmt = stmt.options(*options)

        if ordering is not None:
            if not isinstance(ordering, type(False)):
                stmt = stmt.order_by(ordering)
        else:
            stmt = stmt.order_by(cls.id)

        if limit:
            stmt = stmt.limit(limit)

        return stmt

    @classmethod
    async def add_all(
        cls, items: List[Any], async_session: async_sessionmaker[AsyncSession]
    ) -> None:
        """
        Добавить все элементы в таблицу.
        """
        async with async_session() as session:
            async with session.begin():
                session.add_all(items)
                await session.commit()

    @classmethod
    async def add(
        cls, item: Any, async_session: async_sessionmaker[AsyncSession]
    ) -> None:
        """
        Добавить 1 элемент в таблицу.
        """
        async with async_session() as session:
            async with session.begin():
                session.add(item)
                await session.commit()

    @classmethod
    async def delete_all(cls, async_session: async_sessionmaker[AsyncSession]) -> None:
        """
        Удалить все элементы из таблицы.
        """
        async with async_session() as session:
            stmt = delete(cls)

            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def update(
        cls, instances: List[dict], async_session: async_sessionmaker[AsyncSession]
    ) -> None:
        """
        Обновить элементы в таблице.
        """
        async with async_session() as session:
            stmt = update(cls)

            await session.execute(stmt, instances)
            await session.commit()
